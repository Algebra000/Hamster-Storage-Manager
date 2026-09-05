import argparse
import datetime
import json
import sqlite3
from pathlib import Path


REPLY_PAGE_SIZE = 5

def calculate_time_desc(ctime):
    now = datetime.datetime.now().timestamp()
    diff = int(now - ctime)
    if diff < 60:
        return f"{diff}秒前"
    elif diff < 3600:
        return f"{diff // 60}分钟前"
    elif diff < 86400:
        return f"{diff // 3600}小时前"
    else:
        return f"{diff // 86400}天前发布"


css_style_trans_dict = {
    "borderRadius": "border-radius",
    "boxSizing": "box-sizing",
}

def build_avatar_html(avatar_item, base_width, base_height):
    if not avatar_item:
        return ""
    
    container_size = avatar_item.get("container_size", {})
    canvas_width = container_size.get("width", 1.8) * base_width
    canvas_height = container_size.get("height", 1.8) * base_height
    
    layers_data = avatar_item.get("layers", [])
    if not layers_data:
        fallback_layers = avatar_item.get("fallback_layers", {})
        layers_data = fallback_layers.get("layers", [])
    
    layers_html = parse_layers(layers_data, base_width, base_height)
    
    return f'<div class="avatar-canvas" style="width: {int(canvas_width)}px; height: {int(canvas_height)}px;">{layers_html}</div>'


def parse_layers(layers_data, base_width, base_height):
    if not layers_data:
        return ""

    result = ""
    # 栈式DFS：("layer", layer_dict) 处理图层，("close", None) 闭合div
    stack = []
    for layer in reversed(layers_data):
        stack.append(("layer", layer))

    while stack:
        task_type, task_data = stack.pop()

        if task_type == "close":
            result += '</div>'
            continue

        layer = task_data
        visible = layer.get("visible", False)

        general_spec = layer.get("general_spec", {})
        pos_spec = general_spec.get("pos_spec", {})
        size_spec = general_spec.get("size_spec", {})
        render_spec = general_spec.get("render_spec", {})

        coordinate_pos = pos_spec.get("coordinate_pos", 2)
        axis_x = pos_spec.get("axis_x", 0.9)
        axis_y = pos_spec.get("axis_y", 0.9)
        width = size_spec.get("width", 1) * base_width
        height = size_spec.get("height", 1) * base_height
        opacity = render_spec.get("opacity", 1)

        if coordinate_pos == 1:
            x = int(axis_x * base_width)
            y = int(axis_y * base_height)
        else:
            x = int(axis_x * base_width - width / 2)
            y = int(axis_y * base_height - height / 2)

        if visible:
            layer_style = f"left: {x}px; top: {y}px; width: {int(width)}px; height: {int(height)}px;"
        else:
            layer_style = ""
        if opacity != 1:
            layer_style += f" opacity: {opacity};"

        img_html = ""
        if visible:
            resource = layer.get("resource", {})
            res_type = resource.get("res_type", 0)

            if res_type == 4:
                res_animation = resource.get("res_animation", {})
                webp_src = res_animation.get("webp_src", {})
                remote = webp_src.get("remote", {})
                img_url = remote.get("url", "")
            elif res_type == 3:
                res_image = resource.get("res_image", {})
                image_src = res_image.get("image_src", {})
                src_type = image_src.get("src_type", 1)
                if src_type == 2:
                    local_id = image_src.get("local", 0)
                    img_url = f"./bilibili-resource/res-local{local_id}.png"
                else:
                    remote = image_src.get("remote", {})
                    img_url = remote.get("url", "")
            else:
                img_url = ""

            if img_url:
                layer_config = layer.get("layer_config", {})
                tags = layer_config.get("tags", {})
                general_cfg = tags.get("GENERAL_CFG", {})
                general_config = general_cfg.get("general_config", {})
                web_css_style = general_config.get("web_css_style", {})

                img_style_parts = [f"width: {int(width)}px; height: {int(height)}px;"]
                for key, value in web_css_style.items():
                    css_key = css_style_trans_dict.get(key, key)
                    img_style_parts.append(f"{css_key}: {value};")
                img_style = "; ".join(img_style_parts)

                img_html = f'<img src="{img_url}" style="{img_style}">'

        sub_layers = layer.get("layers", [])
        if sub_layers:
            # 先压入闭合任务（最后执行），再压入子图层（逆序保证顺序一致）
            stack.append(("close", None))
            for sub_layer in reversed(sub_layers):
                stack.append(("layer", sub_layer))
            result += f'<div class="avatar-layer" style="{layer_style}">{img_html}'
        else:
            result += f'<div class="avatar-layer" style="{layer_style}">{img_html}</div>'

    return result


style_str = '''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B站评论展示</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            min-height: 100vh;
        }}
        @font-face {{
            font-family: "HarmonyOS_Regular";
            src: url("./bilibili-resource/HarmonyOS-Regular-subset1.woff") format("woff");
        }}
        @font-face {{
            font-family: 'fans-num';
            src: url("./bilibili-resource/fans-num.ttf") format("truetype");
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #fb7299 0%, #ff7cce 100%);
            color: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(251, 114, 153, 0.3);
        }}
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .comment-list {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }}
        .comment-item {{
            padding: 16px 0;
            border-bottom: 1px solid #f0f0f0;
            position: relative;
        }}
        .comment-item:last-child {{
            border-bottom: none;
        }}
        .comment-header {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        .avatar {{
            width: 48px;
            height: 48px;
            margin-right: 12px;
            flex-shrink: 0;
            border: 2px solid transparent;
            position: relative;
            overflow: visible;
        }}
        .avatar-canvas {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        .avatar-layer {{
            position: absolute;
        }}
        .avatar-layer img {{
            display: block;
        }}
        .user-info {{
            flex: 1;
            min-width: 0;
        }}
        .username {{
            font-weight: 600;
            font-size: 15px;
            color: #18191c;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .level-badge {{
            width: 30px;
            height: 30px;
        }}
        .vip-username {{
            color: #fb7299;
        }}
        .reply-username.vip-username {{
            color: #fb7299;
        }}
        .vip-avatar-badge {{
            position: absolute;
            bottom: 0;
            right: 0;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid white;
            box-sizing: content-box;
            z-index: 2;
        }}
        .meta-info {{
            font-size: 12px;
            color: #9499a0;
            display: flex;
            gap: 12px;
        }}
        .comment-content {{
            margin-left: 60px;
            margin-bottom: 12px;
            line-height: 24px;
            font-size: 15px;
            color: #18191c;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .comment-content img {{
            vertical-align: text-bottom;
            max-height: 24px;
            margin: 0 2px;
        }}
        .comment-picture {{
            margin-left: 60px;
            margin-top: 8px;
            margin-bottom: 6px;
        }}
        .comment-picture.single img {{
            max-width: 210px;
            max-height: 180px;
            border-radius: 6px;
            cursor: zoom-in;
        }}
        .comment-picture.grid {{
            display: grid;
            grid-template-columns: repeat(4, 92px);
            gap: 4px;
        }}
        .comment-picture.grid .picture-item {{
            width: 88px;
            height: 88px;
            border-radius: 6px;
            overflow: hidden;
            cursor: zoom-in;
            position: relative;
        }}
        .comment-picture.grid .picture-item img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .image-preview-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        .image-preview-modal.active {{
            display: flex;
        }}
        .image-preview-modal img {{
            max-width: 90%;
            max-height: 90%;
            cursor: zoom-in;
            transition: transform 0.2s ease;
        }}
        .image-preview-modal img.zoomed {{
            max-width: none;
            max-height: none;
            cursor: grab;
        }}
        .image-preview-modal img.zoomed:active {{
            cursor: grabbing;
        }}
        .image-preview-modal .close-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
        }}
        .image-preview-modal .nav-btn {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 44px;
            height: 44px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            cursor: pointer;
            user-select: none;
        }}
        .image-preview-modal .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.4);
        }}
        .image-preview-modal .nav-btn.disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        .image-preview-modal .nav-btn.disabled:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        .image-preview-modal .prev-btn {{
            left: 20px;
        }}
        .image-preview-modal .next-btn {{
            right: 20px;
        }}
        .image-preview-modal .image-counter {{
            position: absolute;
            top: 20px;
            left: 20px;
            font-family: "HarmonyOS_Regular";
            font-size: 16px;
            color: white;
            background: rgba(0, 0, 0, 0.5);
            padding: 6px 12px;
            border-radius: 4px;
        }}
        .comment-item {{
            position: relative;
        }}
        .cardBg {{
            position: absolute;
            top: 0;
            right: 0;
            height: 48px;
            cursor: pointer;
            display: flex;
            align-items: center;
        }}
        .cardBg img {{
            height: 100%;
            border-radius: 4px;
        }}
        .cardBg .card-text {{
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            font-family: 'fans-num';
            font-size: 10px;
            line-height: 12px;
            text-align: left;
            display: flex;
            flex-direction: column;
            padding-right: 4px;
        }}
        .cardBg .card-text span {{
            display: block;
        }}
        .cardBg .tooltip {{
            display: none;
            position: absolute;
            top: calc(100% - 10px);
            left: calc(100% - 20px);
            border: 1px solid gainsboro;
            background: white;
            color: black;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 100;
            margin-bottom: 8px;
            box-shadow: rgba(0, 0, 0, 0.1) 0px 0px 30px 2px;
        }}
        .cardBg:hover .tooltip {{
            display: block;
        }}
        .cardBg .tooltip .tooltip-name {{
            font-weight: bold;
            margin-bottom: 4px;
        }}
        .cardBg .tooltip .tooltip-id {{
            color: #9499a0;
        }}
        .comment-footer {{
            margin-left: 60px;
            display: flex;
            align-items: center;
            gap: 24px;
        }}
        .action-btn {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #9499a0;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .action-btn:hover {{
            color: #00A1D6;
        }}
        .action-btn:hover img {{
            filter: invert(39%) sepia(90%) saturate(2000%) hue-rotate(170deg) brightness(95%) contrast(100%);
        }}
        .action-btn span {{
            font-weight: 500;
        }}
        .jump-link {{
            color: #008AC5;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 1px;
            vertical-align: bottom;
        }}
        .jump-link:hover {{
            color: #00aeec;
        }}
        .timestamp {{
            color: #9499a0;
            font-size: 13px;
            font-family: "HarmonyOS_Regular",Helvetica Neue, Microsoft YaHei, sans-serif !important;
        }}
        .reply-section {{
            margin-top: 12px;
            margin-left: 60px;
            padding-left: 16px;
            border-left: 2px solid #e9e9eb;
        }}
        .reply-item {{
            padding: 12px 0;
            border-bottom: 1px solid #f5f5f5;
        }}
        .reply-item:last-child {{
            border-bottom: none;
        }}
        .reply-header {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        .reply-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            overflow: visible;
            margin-right: 10px;
            flex-shrink: 0;
            position: relative;
        }}
        .reply-avatar .avatar-canvas {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        .reply-avatar .avatar-layer {{
            position: absolute;
        }}
        .reply-avatar .avatar-layer img {{
            display: block;
        }}
        .reply-username {{
            font-weight: 500;
            font-size: 14px;
            color: #18191c;
            margin-bottom: 2px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .reply-meta {{
            font-size: 11px;
            color: #9499a0;
        }}
        .reply-content {{
            margin-left: 46px;
            line-height: 1.6;
            font-size: 14px;
            color: #18191c;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .reply-content img {{
            vertical-align: text-bottom;
            max-height: 20px;
            margin: 0 2px;
        }}
        .reply-footer {{
            margin-left: 46px;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 24px;
        }}
        .expand-btn {{
            margin-left: 60px;
            margin-top: 8px;
            color: #00a1d6;
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        .expand-btn:hover {{
            text-decoration: underline;
        }}
        .reply-expand-btn {{
            margin-top: 8px;
            color: #9499a0;
            font-size: 13px;
            cursor: pointer;
        }}
        .reply-expand-btn:hover {{
            color: #00a1d6;
        }}
        .reply-pagination {{
            margin-left: 60px;
            margin-top: 12px;
            margin-bottom: 8px;
            font-size: 13px;
            color: #000000;
            display: flex;
            align-items: center;
            gap: 4px;
            flex-wrap: wrap;
            bottom: 0;
            background: white;
            z-index: 10;
        }}
        .reply-pagination .page-count {{
            margin-right: 10px;
        }}
        .reply-pagination .page-num {{
            color: #000000;
            cursor: pointer;
            padding: 2px 1px;
        }}
        .reply-pagination .page-num:hover {{
            color: #00AEEC;
        }}
        .reply-pagination .page-num.active {{
            color: #00AEEC;
        }}
        .reply-pagination .page-ellipsis {{
            color: #000000;
        }}
        .reply-pagination .page-btn {{
            color: #000000;
            cursor: pointer;
        }}
        .reply-pagination .page-btn:hover {{
            color: #00AEEC;
        }}
        .count-badge {{
            display: inline-block;
            background: #f4f4f4;
            color: #9499a0;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
        }}
    </style>'''

script_str = """<script>
        var isZoomed = false;
        var isDragging = false;
        var dragMoved = false;
        var startX, startY, translateX = 0, translateY = 0;
        var currentImages = [];
        var currentIndex = 0;
        const REPLY_PAGE_SIZE = """ + str(REPLY_PAGE_SIZE) + """;

        function previewImage(images, index) {{
            if (typeof images === 'string') {{
                currentImages = [images];
                currentIndex = 0;
            }} else {{
                currentImages = images;
                currentIndex = index;
            }}
            showImage();
            var modal = document.getElementById('imagePreviewModal');
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function showImage() {{
            var img = document.getElementById('previewImage');
            img.src = currentImages[currentIndex];
            img.classList.remove('zoomed');
            img.style.transform = 'translate(0, 0)';
            isZoomed = false;
            isDragging = false;
            dragMoved = false;
            translateX = 0;
            translateY = 0;
            updateNavButtons();
            updateImageCounter();
        }}

        function updateImageCounter() {{
            var counter = document.getElementById('imageCounter');
            if (currentImages.length > 1) {{
                counter.textContent = (currentIndex + 1) + ' / ' + currentImages.length;
            }} else {{
                counter.textContent = '';
            }}
        }}

        function updateNavButtons() {{
            var prevBtn = document.getElementById('prevBtn');
            var nextBtn = document.getElementById('nextBtn');
            prevBtn.classList.toggle('disabled', currentIndex <= 0);
            nextBtn.classList.toggle('disabled', currentIndex >= currentImages.length - 1);
        }}

        function navigatePreview(direction) {{
            var newIndex = currentIndex + direction;
            if (newIndex < 0 || newIndex >= currentImages.length) return;
            currentIndex = newIndex;
            showImage();
        }}

        function closePreview() {{
            var modal = document.getElementById('imagePreviewModal');
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }}

        document.getElementById('previewImage').addEventListener('click', function(e) {{
            e.stopPropagation();
            if (dragMoved) {{
                dragMoved = false;
                return;
            }}
            if (!isZoomed) {{
                this.classList.add('zoomed');
                isZoomed = true;
            }} else {{
                this.classList.remove('zoomed');
                this.style.transform = 'translate(0, 0)';
                isZoomed = false;
                translateX = 0;
                translateY = 0;
            }}
        }});

        document.getElementById('previewImage').addEventListener('mousedown', function(e) {{
            if (!isZoomed) return;
            e.preventDefault();
            isDragging = true;
            dragMoved = false;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
        }});

        document.addEventListener('mousemove', function(e) {{
            if (!isZoomed || !isDragging) return;
            dragMoved = true;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            document.getElementById('previewImage').style.transform = 'translate(' + translateX + 'px, ' + translateY + 'px)';
        }});

        document.addEventListener('mouseup', function(e) {{
            if (!isZoomed) return;
            isDragging = false;
        }});

        document.getElementById('imagePreviewModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closePreview();
            }}
        }});

        function toggleReplies(commentId, totalCount) {{
            var container = document.getElementById('reply-container-' + commentId);
            var expandBtn = document.querySelector('.reply-section #reply-container-' + commentId + ' + .reply-expand-btn');
            var pagination = document.getElementById('reply-pagination-' + commentId);
            var items = container.querySelectorAll('.reply-item');
            
            var isCollapsed = expandBtn && expandBtn.style.display !== 'none';
            
            if (isCollapsed) {{
                var showCount = totalCount <= REPLY_PAGE_SIZE ? totalCount : REPLY_PAGE_SIZE;
                for (var i = 0; i < items.length; i++) {{
                    if (i < showCount) {{
                        items[i].style.display = '';
                    }} else {{
                        items[i].style.display = 'none';
                    }}
                }}
                if (expandBtn) expandBtn.style.display = 'none';
                if (pagination && totalCount > REPLY_PAGE_SIZE) {{
                    pagination.style.display = '';
                    updatePagination(commentId, 1, totalCount);
                }}
            }} else {{
                for (var i = 0; i < items.length; i++) {{
                    if (i < 2) {{
                        items[i].style.display = '';
                    }} else {{
                        items[i].style.display = 'none';
                    }}
                }}
                if (expandBtn) expandBtn.style.display = '';
                if (pagination) pagination.style.display = 'none';
            }}
        }}

        function showReplyPage(commentId, pageNum, totalCount) {{
            var container = document.getElementById('reply-container-' + commentId);
            var items = container.querySelectorAll('.reply-item');
            var startIndex = (pageNum - 1) * REPLY_PAGE_SIZE;
            var endIndex = startIndex + REPLY_PAGE_SIZE;
            
            for (var i = 0; i < items.length; i++) {{
                if (i >= startIndex && i < endIndex) {{
                    items[i].style.display = '';
                }} else {{
                    items[i].style.display = 'none';
                }}
            }}
            
            var pagination = document.getElementById('reply-pagination-' + commentId);
            updatePagination(commentId, pageNum, totalCount);
        }}

        function updatePagination(commentId, currentPage, totalCount) {{
            var pagination = document.getElementById('reply-pagination-' + commentId);
            var totalPages = Math.ceil(totalCount / REPLY_PAGE_SIZE);
            
            var html = '<span class="page-count">共' + totalPages + '页</span>';
            
            if (currentPage > 1) {{
                html += '<span class="page-btn" onclick="showReplyPage(' + commentId + ', ' + (currentPage - 1) + ', ' + totalCount + ')">上一页</span>';
            }}
            
            if (totalPages <= 6) {{
                for (var i = 1; i <= totalPages; i++) {{
                    html += '<span class="page-num' + (i === currentPage ? ' active' : '') + '" onclick="showReplyPage(' + commentId + ', ' + i + ', ' + totalCount + ')">' + i + '</span>';
                }}
            }} else {{
                if (currentPage <= 3) {{
                    for (var i = 1; i <= 5; i++) {{
                        html += '<span class="page-num' + (i === currentPage ? ' active' : '') + '" onclick="showReplyPage(' + commentId + ', ' + i + ', ' + totalCount + ')">' + i + '</span>';
                    }}
                    html += '<span class="page-ellipsis">...</span>';
                    html += '<span class="page-num" onclick="showReplyPage(' + commentId + ', ' + totalPages + ', ' + totalCount + ')">' + totalPages + '</span>';
                }} else if (currentPage >= totalPages - 2) {{
                    html += '<span class="page-num" onclick="showReplyPage(' + commentId + ', 1, ' + totalCount + ')">1</span>';
                    html += '<span class="page-ellipsis">...</span>';
                    for (var i = totalPages - 4; i <= totalPages; i++) {{
                        html += '<span class="page-num' + (i === currentPage ? ' active' : '') + '" onclick="showReplyPage(' + commentId + ', ' + i + ', ' + totalCount + ')">' + i + '</span>';
                    }}
                }} else {{
                    html += '<span class="page-num" onclick="showReplyPage(' + commentId + ', 1, ' + totalCount + ')">1</span>';
                    html += '<span class="page-ellipsis">...</span>';
                    for (var i = currentPage - 2; i <= currentPage + 2; i++) {{
                        html += '<span class="page-num' + (i === currentPage ? ' active' : '') + '" onclick="showReplyPage(' + commentId + ', ' + i + ', ' + totalCount + ')">' + i + '</span>';
                    }}
                    html += '<span class="page-ellipsis">...</span>';
                    html += '<span class="page-num" onclick="showReplyPage(' + commentId + ', ' + totalPages + ', ' + totalCount + ')">' + totalPages + '</span>';
                }}
            }}
            
            if (currentPage < totalPages) {{
                html += '<span class="page-btn" onclick="showReplyPage(' + commentId + ', ' + (currentPage + 1) + ', ' + totalCount + ')">下一页</span>';
            }}
            
            html += '<span class="page-btn" onclick="toggleReplies(' + commentId + ', ' + totalCount + ')">收起</span>';
            
            pagination.innerHTML = html;
        }}
    </script>"""


html_template = """<!DOCTYPE html>
<html lang="zh-CN">
""" + style_str + """
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 B站评论展示</h1>
            <p>共 <strong>{comment_count}</strong> 条评论</p>
        </div>
        <div class="comment-list">
            {comments_html}
        </div>
    </div>
    <div class="image-preview-modal" id="imagePreviewModal">
        <div class="close-btn" onclick="closePreview()">
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="20" viewBox="0 0 20 20">
                <path d="M4.106275 4.108583333333334C4.350341666666667 3.8645000000000005 4.746083333333333 3.8645000000000005 4.9901583333333335 4.108583333333334L9.998666666666667 9.117125L15.008583333333334 4.107216666666667C15.252625 3.8631333333333338 15.648375000000001 3.8631333333333338 15.892458333333334 4.107216666666667C16.136541666666666 4.351291666666667 16.136541666666666 4.747025000000001 15.892458333333334 4.9911L10.882541666666667 10.001000000000001L15.891375 15.009791666666667C16.135458333333332 15.253874999999999 16.135458333333332 15.649625 15.891375 15.893708333333334C15.647291666666668 16.13775 15.251541666666668 16.13775 15.0075 15.893708333333334L9.998666666666667 10.884875000000001L4.991233333333334 15.892333333333333C4.747158333333333 16.13641666666667 4.351425 16.13641666666667 4.10735 15.892333333333333C3.8632750000000002 15.648249999999999 3.8632750000000002 15.252541666666666 4.10735 15.008458333333333L9.114791666666667 10.001000000000001L4.106275 4.992466666666667C3.8621916666666665 4.7483916666666675 3.8621916666666665 4.352658333333333 4.106275 4.108583333333334z" fill="currentColor"></path>
            </svg>
        </div>
        <div class="image-counter" id="imageCounter"></div>
        <div class="nav-btn prev-btn" id="prevBtn" onclick="navigatePreview(-1)">
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="20" viewBox="0 0 20 20">
                <path d="M12.733583333333334 2.6830583333333333C12.977666666666668 2.927141666666667 12.977666666666668 3.3228666666666666 12.733583333333334 3.566941666666667L6.595175 9.705375C6.432458333333334 9.868125 6.432458333333334 10.131875 6.595175 10.294625L12.733583333333334 16.433041666666668C12.977666666666668 16.677125 12.977666666666668 17.072875 12.733583333333334 17.316958333333332C12.489541666666668 17.561 12.093791666666666 17.561 11.849708333333334 17.316958333333332L5.711291666666667 11.1785C5.060416666666667 10.527625 5.060416666666667 9.472375 5.711291666666667 8.8215L11.849708333333334 2.6830583333333333C12.093791666666666 2.4389833333333333 12.489541666666668 2.4389833333333333 12.733583333333334 2.6830583333333333z" fill="currentColor"></path>
            </svg>
        </div>
        <img id="previewImage" src="" alt="预览图片">
        <div class="nav-btn next-btn" id="nextBtn" onclick="navigatePreview(1)">
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="20" viewBox="0 0 20 20" style="transform: rotate(180deg);">
                <path d="M12.733583333333334 2.6830583333333333C12.977666666666668 2.927141666666667 12.977666666666668 3.3228666666666666 12.733583333333334 3.566941666666667L6.595175 9.705375C6.432458333333334 9.868125 6.432458333333334 10.131875 6.595175 10.294625L12.733583333333334 16.433041666666668C12.977666666666668 16.677125 12.977666666666668 17.072875 12.733583333333334 17.316958333333332C12.489541666666668 17.561 12.093791666666666 17.561 11.849708333333334 17.316958333333332L5.711291666666667 11.1785C5.060416666666667 10.527625 5.060416666666667 9.472375 5.711291666666667 8.8215L11.849708333333334 2.6830583333333333C12.093791666666666 2.4389833333333333 12.489541666666668 2.4389833333333333 12.733583333333334 2.6830583333333333z" fill="currentColor"></path>
            </svg>
        </div>
    </div>
    """ + script_str + """
</body>
</html>"""


def comment_to_comment_html(comment):
    '''
    将一条评论转换为对应的HTML字符串
    '''
    comment_id = comment.get("rpid", 0)
    member = comment.get("member", {})
    content = comment.get("content", {})
    reply_control = comment.get("reply_control", {})
    replies = comment.get("replies", []) or []

    username = member.get("uname", "匿名用户")
    level = member.get("level_info", {}).get("current_level", 0)
    vip_status = member.get("vip", {}).get("vipStatus", 0)
    is_senior_member = member.get("is_senior_member", 0)
    avatar_item = member.get("avatar_item", {})

    is_vip = vip_status == 1
    username_class = "username vip-username" if is_vip else "username"
    avatar_html = build_avatar_html(avatar_item, 48, 48)

    level_svg = "level_h.svg" if (level == 6 and is_senior_member == 1) else f"level_{level}.svg"

    message = content.get("message", "")
    emotes = content.get("emote", {}) or {}
    jump_url = content.get("jump_url", {}) or {}
    pictures = content.get("pictures", []) or []

    message_html = message
    for emote_key, emote_data in emotes.items():
        emote_url = emote_data.get("url", "")
        emote_meta = emote_data.get("meta", {}) or {}
        emote_size = emote_meta.get("size", 1)
        if emote_url:
            if emote_size == 1:
                message_html = message_html.replace(
                    emote_key,
                    f'<img src="{emote_url}" alt="{emote_key}" title="{emote_data.get("text", "")}">'
                )
            else:
                max_width = 25*int(emote_size)
                max_height = max_width
                message_html = message_html.replace(
                    emote_key,
                    f'<img src="{emote_url}" alt="{emote_key}" title="{emote_data.get("text", "")}" style="max-width: {max_width}px; max-height: {max_height}px;">'
                )

    for url, url_data in jump_url.items():
        prefix_icon = url_data.get("prefix_icon", "")
        title = url_data.get("title", "")
        pc_url = url_data.get("pc_url", "")
        icon_position = url_data.get("icon_position", 0)
        if pc_url.startswith("//"):
            pc_url = "https:" + pc_url
        if pc_url:
            if prefix_icon and title and icon_position == 0:
                jump_html = f'<a href="{pc_url}" class="jump-link" target="_blank"><img src="{prefix_icon}" alt="链接" width="18" height="18">{title}</a>'
                message_html = message_html.replace(url, jump_html)
            elif prefix_icon and title and icon_position == 1:
                jump_html = f'<a href="{pc_url}" class="jump-link" target="_blank">{title}<img src="{prefix_icon}" alt="链接" style="max-width: 18px; max-height: 18px; margin: 0px;"></a>'
                message_html = message_html.replace(url, jump_html)
        else:
            if prefix_icon and title and icon_position == 0:
                jump_html = f'<a href="{url}" class="jump-link" target="_blank"><img src="{prefix_icon}" alt="链接" width="18" height="18">{title}</a>'
                message_html = message_html.replace(url, jump_html)
            elif prefix_icon and title and icon_position == 1:
                jump_html = f'<a href="{url}" class="jump-link" target="_blank">{title}<img src="{prefix_icon}" alt="链接" style="max-width: 18px; max-height: 18px; margin: 0px;"></a>'
                message_html = message_html.replace(url, jump_html)

    pictures_html = ""
    all_srcs = [pic.get("img_src", "") for pic in pictures if pic.get("img_src")]
    if len(all_srcs) == 1:
        img_src = all_srcs[0]
        pictures_html = f'\n            <div class="comment-picture single"><img src="{img_src}" alt="评论图片" onclick="previewImage(\'{img_src}\')"></div>'
    elif len(all_srcs) > 1:
        js_array = "[" + ", ".join(f"'{s}'" for s in all_srcs) + "]"
        pictures_html = '\n            <div class="comment-picture grid">'
        for i, img_src in enumerate(all_srcs):
            pictures_html += f'\n                <div class="picture-item" onclick="previewImage({js_array}, {i})"><img src="{img_src}" alt="评论图片"></div>'
        pictures_html += '\n            </div>'

    like_count = comment.get("like", 0)
    like_count_html = f'<span>{like_count}</span>' if like_count > 0 else ''
    location = reply_control.get("location", "")
    ctime = comment.get("ctime", 0)
    time_desc = calculate_time_desc(ctime)
    timestamp = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S")

    cardbg_html = ""
    user_sailing = member.get("user_sailing", {})
    if user_sailing and "cardbg" in user_sailing:
        cardbg = user_sailing["cardbg"]
        if cardbg:
            cardbg_image = cardbg.get("image", "")
            cardbg_jump_url = cardbg.get("jump_url", "")
            cardbg_name = cardbg.get("name", "")
            cardbg_id = cardbg.get("id", "")
            fan = cardbg.get("fan", {})
            num_prefix = fan.get("num_prefix", "")
            num_desc = fan.get("num_desc", "")
            color_format = fan.get("color_format", {})
            if type(color_format) != dict:
                color_format = {}
            colors = color_format.get("colors", ["#B8C7D0FF", "#A2A7B0FF"])
            gradients = color_format.get("gradients", [0, 100])
            gradient_parts = []
            for i, color in enumerate(colors):
                color_hex = color.replace("FF", "") if color.endswith("FF") else color
                percent = gradients[i] if i < len(gradients) else (100 if i == len(colors) - 1 else 0)
                gradient_parts.append(f"{color_hex} {percent}%")
            gradient_style = f"background-image: linear-gradient(135deg, {', '.join(gradient_parts)}); -webkit-text-fill-color: transparent; background-clip: text;"
            cardbg_html = f"""
            <a href="{cardbg_jump_url}" class="cardBg" target="_blank">
                <img src="{cardbg_image}" alt="{cardbg_name}">
                <div class="card-text" style="{gradient_style}">
                    <span>{num_prefix}</span>
                    <span>{num_desc}</span>
                </div>
                <div class="tooltip">
                    <div class="tooltip-name">{cardbg_name}</div>
                    <div class="tooltip-id">ID: {cardbg_id}</div>
                </div>
            </a>"""

    mid = member.get("mid", "")
    profile_url = f"https://space.bilibili.com/{mid}" if mid else ""

    comment_html = f"""
        <div class="comment-item">
            {cardbg_html}
            <div class="comment-header">
                <a href="{profile_url}" class="avatar" target="_blank">
                    {avatar_html}
                </a>
                <div class="user-info">
                    <div class="{username_class}">
                        {username}
                        <img class="level-badge" src="./bilibili-resource/{level_svg}" alt="Lv.{level}">
                    </div>
                    <div class="meta-info">
                        <span>{time_desc}</span>
                        {f'<span>{location}</span>' if location else ''}
                    </div>
                </div>
            </div>
            <div class="comment-content">{message_html}</div>{pictures_html}
            <div class="comment-footer">
                <span class="timestamp">{timestamp}</span>
                <div class="action-btn">
                    <img src="./bilibili-resource/like.svg" alt="赞" width="16" height="16">
                    {like_count_html}
                </div>
                <div class="action-btn">
                    <img src="./bilibili-resource/dislike.svg" alt="踩" width="16" height="16">
                </div>
            </div>"""

    if replies:
        total_replies = len(replies)
        comment_html += f"""
            <div class="reply-section">
                <div class="reply-container" id="reply-container-{comment_id}">"""
        
        for idx, reply in enumerate(replies):
            reply_member = reply.get("member", {})
            reply_content = reply.get("content", {})
            reply_reply_control = reply.get("reply_control", {})

            reply_username = reply_member.get("uname", "匿名用户")
            reply_level = reply_member.get("level_info", {}).get("current_level", 0)
            reply_vip_status = reply_member.get("vip", {}).get("vipStatus", 0)
            reply_is_senior_member = reply_member.get("is_senior_member", 0)
            reply_avatar_item = reply_member.get("avatar_item", {})

            reply_is_vip = reply_vip_status == 1
            reply_username_class = "reply-username vip-username" if reply_is_vip else "reply-username"
            reply_avatar_html = build_avatar_html(reply_avatar_item, 36, 36)

            reply_level_svg = "level_h.svg" if (reply_level == 6 and reply_is_senior_member == 1) else f"level_{reply_level}.svg"

            reply_message = reply_content.get("message", "")
            reply_emotes = reply_content.get("emote", {}) or {}
            reply_jump_url = reply_content.get("jump_url", {}) or {}
            reply_pictures = reply_content.get("pictures", []) or []

            reply_message_html = reply_message
            for emote_key, emote_data in reply_emotes.items():
                emote_url = emote_data.get("url", "")
                emote_meta = emote_data.get("meta", {}) or {}
                emote_size = emote_meta.get("size", 1)
                if emote_url:
                    if emote_size == 1:
                        reply_message_html = reply_message_html.replace(
                            emote_key,
                            f'<img src="{emote_url}" alt="{emote_key}" title="{emote_data.get("text", "")}">'
                        )
                    else:
                        max_width = 25*int(emote_size)
                        max_height = max_width
                        reply_message_html = reply_message_html.replace(
                            emote_key,
                            f'<img src="{emote_url}" alt="{emote_key}" title="{emote_data.get("text", "")}" style="max-width: {max_width}px; max-height: {max_height}px;">'
                        )

            for url, url_data in reply_jump_url.items():
                prefix_icon = url_data.get("prefix_icon", "")
                title = url_data.get("title", "")
                pc_url = url_data.get("pc_url", "")
                icon_position = url_data.get("icon_position", 0)
                if pc_url.startswith("//"):
                    pc_url = "https:" + pc_url
                if pc_url:
                    if prefix_icon and title and icon_position == 0:
                        jump_html = f'<a href="{pc_url}" class="jump-link" target="_blank"><img src="{prefix_icon}" alt="链接" width="18" height="18">{title}</a>'
                        reply_message_html = reply_message_html.replace(url, jump_html)
                    elif prefix_icon and title and icon_position == 1:
                        jump_html = f'<a href="{pc_url}" class="jump-link" target="_blank">{title}<img src="{prefix_icon}" alt="链接" style="max-width: 18px; max-height: 18px; margin: 0px;"></a>'
                        reply_message_html = reply_message_html.replace(url, jump_html)
                else:
                    if prefix_icon and title and icon_position == 0:
                        jump_html = f'<a href="{url}" class="jump-link" target="_blank"><img src="{prefix_icon}" alt="链接" width="18" height="18">{title}</a>'
                        reply_message_html = reply_message_html.replace(url, jump_html)
                    elif prefix_icon and title and icon_position == 1:
                        jump_html = f'<a href="{url}" class="jump-link" target="_blank">{title}<img src="{prefix_icon}" alt="链接" style="max-width: 18px; max-height: 18px; margin: 0px;"></a>'
                        reply_message_html = reply_message_html.replace(url, jump_html)

            reply_pictures_html = ""
            reply_all_srcs = [pic.get("img_src", "") for pic in reply_pictures if pic.get("img_src")]
            if len(reply_all_srcs) == 1:
                img_src = reply_all_srcs[0]
                reply_pictures_html = f'\n                        <div class="comment-picture single"><img src="{img_src}" alt="评论图片" onclick="previewImage(\'{img_src}\')"></div>'
            elif len(reply_all_srcs) > 1:
                js_array = "[" + ", ".join(f"'{s}'" for s in reply_all_srcs) + "]"
                reply_pictures_html = '\n                        <div class="comment-picture grid">'
                for i, img_src in enumerate(reply_all_srcs):
                    reply_pictures_html += f'\n                            <div class="picture-item" onclick="previewImage({js_array}, {i})"><img src="{img_src}" alt="评论图片"></div>'
                reply_pictures_html += '\n                        </div>'

            reply_like = reply.get("like", 0)
            reply_like_html = f'<span>{reply_like}</span>' if reply_like > 0 else ''
            reply_location = reply_reply_control.get("location", "")
            reply_ctime = reply.get("ctime", 0)
            reply_time = calculate_time_desc(reply_ctime)
            reply_timestamp = datetime.datetime.fromtimestamp(reply_ctime).strftime("%Y-%m-%d %H:%M:%S")
            reply_mid = reply_member.get("mid", "")
            reply_profile_url = f"https://space.bilibili.com/{reply_mid}" if reply_mid else ""

            display_style = ' style="display: none;"' if total_replies > 2 and idx >= 2 else ''

            comment_html += f"""
                    <div class="reply-item" data-reply-index="{idx}"{display_style}>
                        <div class="reply-header">
                            <a href="{reply_profile_url}" class="reply-avatar" target="_blank">
                                {reply_avatar_html}
                            </a>
                            <div>
                                <div class="{reply_username_class}">
                                    {reply_username}
                                    <img class="level-badge" src="./bilibili-resource/{reply_level_svg}" alt="Lv.{reply_level}">
                                </div>
                                <div class="reply-meta">
                                    {reply_time}
                                    {f' · {reply_location}' if reply_location else ''}
                                </div>
                            </div>
                        </div>
                        <div class="reply-content">{reply_message_html}</div>{reply_pictures_html}
                        <div class="reply-footer">
                            <span class="timestamp">{reply_timestamp}</span>
                            <div class="action-btn">
                                <img src="./bilibili-resource/like.svg" alt="赞" width="16" height="16">
                                {reply_like_html}
                            </div>
                            <div class="action-btn">
                                <img src="./bilibili-resource/dislike.svg" alt="踩" width="16" height="16">
                            </div>
                        </div>
                    </div>"""
        
        comment_html += """
                </div>"""
        
        if total_replies > 2:
            expand_display = ''
            if total_replies <= REPLY_PAGE_SIZE:
                pagination_display = ' style="display: none;"'
                pagination_html = ''
            else:
                pagination_display = ' style="display: none;"'
                total_pages = (total_replies + REPLY_PAGE_SIZE - 1) // REPLY_PAGE_SIZE
                pagination_html = f'<span class="page-count">共{total_pages}页</span><span class="page-num active">1</span>'
                if total_pages > 1:
                    pagination_html += f'<span class="page-btn" onclick="showReplyPage({comment_id}, 2, {total_replies})">下一页</span>'
                pagination_html += f'<span class="page-btn" onclick="toggleReplies({comment_id}, {total_replies})">收起</span>'
            
            comment_html += f"""
                <div class="reply-expand-btn"{expand_display} onclick="toggleReplies({comment_id}, {total_replies})">共{total_replies}条回复，点击查看</div>"""
            
            if total_replies > REPLY_PAGE_SIZE:
                comment_html += f"""
                <div class="reply-pagination" id="reply-pagination-{comment_id}"{pagination_display}>
                    {pagination_html}
                </div>"""
        
        comment_html += """
            </div>"""

    comment_html += """
        </div>"""
    return comment_html


def generate_html(comments):
    comments_html = ""
    for comment in comments:
        comments_html += comment_to_comment_html(comment)
    return html_template.format(comment_count=len(comments), comments_html=comments_html)


DATABASE_SCHEMA_VERSION = "v1.1"
REPLY_CONTROL_FIELDS = (
    "max_line", "location", "translation_switch", "support_share",
)

# v1.1 把字典/列表保存成紧凑 JSON 文本。可视化只需还原下列 member/content 字段；
# message、uname、avatar 等普通字符串保持原值，避免把形似 JSON 的评论正文误解析。
ENTITY_JSON_COLUMNS = {
    "member": {
        "senior", "level_info", "pendant", "nameplate", "official_verify",
        "vip", "fans_detail", "user_sailing", "user_sailing_v2",
        "nft_interaction", "avatar_item",
    },
    "content": {
        "members", "jump_url", "pictures", "emote",
        "at_name_to_mid", "at_name_to_mid_str",
    },
}


def decode_entity_value(table_name, column_name, value):
    """只对确定为结构化数据的列执行 json.loads。"""
    if value is None or column_name not in ENTITY_JSON_COLUMNS[table_name]:
        return value
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{table_name}.{column_name} 不是有效的 JSON 文本"
        ) from error


def decode_reply_control(value):
    """把数据库文本恢复为字典，并再次执行四键白名单。"""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("reply_control 不是有效的 JSON 文本") from error
    if not isinstance(value, dict):
        raise ValueError("reply_control 解码后必须是字典")
    return {key:value[key] for key in REPLY_CONTROL_FIELDS if key in value}


def chunks(values, size=800):
    """避免一次查询超过 SQLite 的参数数量限制。"""
    for start in range(0, len(values), size):
        yield values[start:start + size]


def load_entity_rows(connection, table_name, parent_ids):
    """只读取选中评论对应的 member/content 一对一数据。"""
    result = {}
    parent_ids = sorted(set(parent_ids))
    for group in chunks(parent_ids):
        placeholders = ",".join("?" for _ in group)
        sql = f'SELECT * FROM "{table_name}" WHERE parent IN ({placeholders})'
        for row in connection.execute(sql, group):
            parent = int(row["parent"])
            entity = {}
            for column_name in row.keys():
                if column_name in {"parent", "_comment_kind", "_data_hash"}:
                    continue
                value = row[column_name]
                # v1.1 不记录 _present_keys，因此无法区分原键缺失和显式 null。
                # 两者都省略，让原可视化逻辑使用 dict.get(...) 的安全默认值。
                if value is None:
                    continue
                entity[column_name] = decode_entity_value(
                    table_name, column_name, value
                )
            result[parent] = entity
    return result


def table_columns(connection, table_name):
    return [
        row[1]
        for row in connection.execute(f'PRAGMA table_info("{table_name}")')
    ]


def comment_rows_to_dicts(rows, members, contents):
    """把数据库评论行恢复为原可视化函数使用的字典。"""
    result = []
    for row in rows:
        comment = {}
        for column_name in row.keys():
            if column_name.startswith("_") or column_name in {"member", "content"}:
                continue
            value = row[column_name]
            if value is None:
                continue
            if column_name == "reply_control":
                value = decode_reply_control(value)
            comment[column_name] = value
        rpid = int(row["rpid"])
        comment["member"] = members.get(rpid, {})
        comment["content"] = contents.get(rpid, {})
        result.append(comment)
    return result


def integer_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def find_main_rpid(reply, main_ids, replies_by_rpid):
    """优先使用 root；必要时沿 parent 回复链向上寻找主评论。"""
    root = integer_id(reply.get("root_str") or reply.get("root"))
    if root in main_ids:
        return root

    current = integer_id(reply.get("parent_str") or reply.get("parent"))
    visited = set()
    while current is not None and current not in visited:
        if current in main_ids:
            return current
        visited.add(current)
        parent_reply = replies_by_rpid.get(current)
        if parent_reply is None:
            break
        current = integer_id(
            parent_reply.get("parent_str") or parent_reply.get("parent")
        )
    return None


def validate_selection(sortby, from_index, to_index, reverse):
    if sortby not in {"like", "time"}:
        raise ValueError("sortby 只支持 'like' 或 'time'")
    if not isinstance(from_index, int) or isinstance(from_index, bool):
        raise ValueError("from_index 必须是整数")
    if from_index < 0:
        raise ValueError("from_index 不能小于 0")
    if to_index is not None:
        if not isinstance(to_index, int) or isinstance(to_index, bool):
            raise ValueError("to_index 必须是整数或 None")
        if to_index < from_index:
            raise ValueError("to_index 不能小于 from_index")
    if not isinstance(reverse, bool):
        raise ValueError("reverse 必须是布尔值")


def quote_sql_column(column_name):
    """这里只接受内部固定列名；双引号用于兼容 SQLite 标识符。"""
    if column_name not in {"like", "ctime"}:
        raise ValueError(f"不允许的排序列：{column_name}")
    return f'"{column_name}"'


def select_comment_rows(
    connection, table_name, sortby, from_index, to_index, reverse
):
    """在指定顶层评论表中完成排序和局部切片。"""
    if table_name not in {"main", "top"}:
        raise ValueError(f"不允许的顶层评论表：{table_name}")
    sort_column = "like" if sortby == "like" else "ctime"
    columns = set(table_columns(connection, table_name))
    if sort_column not in columns:
        raise ValueError(f"{table_name} 表缺少排序列：{sort_column}")

    direction = "DESC" if reverse else "ASC"
    limit = -1 if to_index is None else to_index - from_index
    sql = (
        f'SELECT * FROM "{table_name}" '
        f'ORDER BY {quote_sql_column(sort_column)} {direction}, '
        f'rpid {direction} LIMIT ? OFFSET ?'
    )
    return connection.execute(sql, (limit, from_index)).fetchall()


def select_main_rows(connection, sortby, from_index, to_index, reverse):
    return select_comment_rows(
        connection, "main", sortby, from_index, to_index, reverse
    )


def select_top_rows(connection, sortby, from_index, to_index, reverse):
    return select_comment_rows(
        connection, "top", sortby, from_index, to_index, reverse
    )


def select_reply_rows(connection, main_ids):
    """只读取 root/parent 能关联到所选主评论的回复。"""
    result = {}
    main_ids = sorted(set(main_ids))
    reply_columns = set(table_columns(connection, "reply"))
    if not main_ids or not {"root", "parent"}.issubset(reply_columns):
        return []

    # root 和 parent 各使用一组参数，因此每块控制在 400 个主键以内。
    for group in chunks(main_ids, 400):
        placeholders = ",".join("?" for _ in group)
        sql = (
            'SELECT * FROM "reply" '
            f'WHERE root IN ({placeholders}) OR parent IN ({placeholders})'
        )
        for row in connection.execute(sql, list(group) + list(group)):
            result[int(row["rpid"])] = row
    return sorted(
        result.values(),
        key=lambda row: (
            integer_id(row["ctime"]) or 0,
            int(row["rpid"]),
        ),
    )


def load_comments_from_database(
    database_path, sortby, from_index, to_index, reverse=True
):
    """从“top + main”连续序列按 [from_index:to_index] 读取并返回 JSON。

    top 和 main 分别按相同规则排序，top 全部位于 main 之前。
    sortby='like' 使用 like 列；sortby='time' 使用 ctime 列。
    reverse=False 为升序，reverse=True 为降序。to_index=None 表示直到末尾。
    """
    validate_selection(sortby, from_index, to_index, reverse)
    database_path = Path(database_path).resolve()
    if not database_path.is_file():
        raise FileNotFoundError(f"未找到评论数据库：{database_path}")

    connection = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required_tables = {"_metadata", "main", "reply", "member", "content"}
        missing_tables = required_tables - tables
        if missing_tables:
            raise ValueError(
                "数据库缺少表：{}".format(", ".join(sorted(missing_tables)))
            )

        metadata = dict(
            connection.execute(
                "SELECT metadata_key, metadata_value FROM _metadata"
            )
        )
        if metadata.get("schema_version") != DATABASE_SCHEMA_VERSION:
            raise ValueError(
                "数据库结构版本为 {!r}，查看器要求 {!r}".format(
                    metadata.get("schema_version"), DATABASE_SCHEMA_VERSION
                )
            )

        top_count = (
            connection.execute('SELECT COUNT(*) FROM "top"').fetchone()[0]
            if "top" in tables else 0
        )
        # 全局区间先与 top 的 [0:top_count] 相交；剩余部分再换算为
        # main 表内部的局部索引。例如 top_count=2、[0:5] 会得到
        # top[0:2] + main[0:3]，最终仍然正好是五条。
        top_rows = []
        if from_index < top_count:
            top_to = top_count if to_index is None else min(to_index, top_count)
            if top_to > from_index:
                top_rows = select_top_rows(
                    connection, sortby, from_index, top_to, reverse
                )

        main_from = max(from_index - top_count, 0)
        main_to = None if to_index is None else max(to_index - top_count, 0)
        main_rows = []
        if main_to is None or main_to > main_from:
            main_rows = select_main_rows(
                connection, sortby, main_from, main_to, reverse
            )
        main_ids = [int(row["rpid"]) for row in main_rows]
        top_ids = [int(row["rpid"]) for row in top_rows]
        parent_ids = top_ids + main_ids
        reply_rows = select_reply_rows(connection, parent_ids)
        all_comment_ids = parent_ids + [int(row["rpid"]) for row in reply_rows]
        members = load_entity_rows(connection, "member", all_comment_ids)
        contents = load_entity_rows(connection, "content", all_comment_ids)
        main_comments = comment_rows_to_dicts(main_rows, members, contents)
        top_comments = comment_rows_to_dicts(top_rows, members, contents)
        replies = comment_rows_to_dicts(reply_rows, members, contents)
    finally:
        connection.close()

    for comment in main_comments + replies:
        comment.pop("is_top", None)
    for comment in top_comments:
        comment["is_top"] = True
    top_level_comments = top_comments + main_comments
    main_by_rpid = {int(item["rpid"]): item for item in top_level_comments}
    replies_by_rpid = {int(item["rpid"]): item for item in replies}
    for comment in top_level_comments:
        comment["replies"] = []

    orphan_count = 0
    main_ids_set = set(main_by_rpid)
    for reply in replies:
        owner_rpid = find_main_rpid(reply, main_ids_set, replies_by_rpid)
        if owner_rpid is None:
            orphan_count += 1
            continue
        main_by_rpid[owner_rpid]["replies"].append(reply)

    if orphan_count:
        print(
            f"警告：选中范围内有 {orphan_count} 条回复无法关联主评论，"
            "已从本次结果中忽略"
        )

    return json.dumps(top_level_comments, ensure_ascii=False, indent=2)

def build_parser():
    script_directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="筛选 v1.1 评论数据库并转换为 JSON/静态 HTML"
    )
    parser.add_argument(
        "database", nargs="?", type=Path,
        default=script_directory / "comment.db",
        help="v1.1 comment.db 路径，默认读取脚本同目录的 comment.db",
    )
    parser.add_argument(
        "--sortby", choices=("like", "time"), default="time",
        help="按点赞数或发布时间排序，默认 time",
    )
    parser.add_argument(
        "--from", dest="from_index", type=int, default=0,
        help="切片起始下标（包含），默认 0",
    )
    parser.add_argument(
        "--to", dest="to_index", type=int,
        help="切片结束下标（不包含），默认直到末尾",
    )
    parser.add_argument(
        "--reverse", action="store_true",default=True,
        help="使用排序；不指定时为降序",
    )
    parser.add_argument(
        "--json-output", type=Path,
        help="可选：把筛选结果同时写入 JSON 文件",
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help="输出 HTML 路径，默认生成在 comment.db 旁边",
    )
    return parser


def main():
    args = build_parser().parse_args()
    try:
        comments_json = load_comments_from_database(
            args.database,
            args.sortby,
            args.from_index,
            args.to_index,
            args.reverse,
        )
        comments = json.loads(comments_json)

        if args.json_output:
            json_path = args.json_output.resolve()
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with json_path.open("w", encoding="utf-8", newline="\n") as file:
                file.write(comments_json)
                file.write("\n")
            print(f"JSON文件已生成：{json_path}")

        html_content = generate_html(comments)
        html_path = (
            args.output
            or Path(args.database).resolve().with_name("comment_viewer(DB).html")
        ).resolve()
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with html_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(html_content)
    except (
        FileNotFoundError, OSError, ValueError,
        json.JSONDecodeError, sqlite3.Error,
    ) as error:
        print(f"生成失败：{error}")
        return 1

    reply_count = sum(len(item.get("replies") or []) for item in comments)
    range_end = "末尾" if args.to_index is None else str(args.to_index)
    print(f"HTML文件已生成：{html_path}")
    print(
        f"排序={args.sortby}，范围=[{args.from_index}:{range_end}]，"
        f"reverse={args.reverse}；展示 {len(comments)} 条主评论、"
        f"{reply_count} 条关联回复"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
