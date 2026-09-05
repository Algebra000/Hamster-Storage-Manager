// 这段代码来自压缩后的产物，因此局部变量名很短。
// _：动画层容器数组（HTMLElement[]），下标与配置数组 f 一一对应。
// f：动画层配置数组（运行时是 Proxy(Array)），每项可配置 scale/rotate/translate/blur/opacity。
// y：每层的初始样式；每帧都从初始值计算，以免多帧累加产生误差。
// b：归一化的水平鼠标位移，而非原始像素距离；V 中用横向像素差除以容器宽度 A 得到。
// v：按容器高度计算的尺寸系数；S：动画帧 id；T：上一次渲染使用的 b。
// I(curve)：把 offsetCurve 配置转换为曲线函数；未配置时直接使用 b。

// 根据当前 b 更新全部动画层。鼠标移动、回中动画和 resize 都会调用它。
const R = () => {
    try {
        // 位移未变化时跳过重复 DOM 写入；resize 会将 T 设为 NaN 来强制重绘。
        if (T === b)
            return;
        T = b,
        _.map( (x, O) => {
            // O 同时是容器 _、配置 f 和初始样式 y 的层下标。
            const M = f[O]
                // 实际接受 transform/filter/opacity 的资源节点。
                , Z = x.firstChild;
            if (!Z)
                return;
            // 先复制初始几何状态，再叠加当前鼠标位移产生的变化。
            const B = {
                scale: y[O].scale,
                rotate: y[O].rotate,
                translate: y[O].translate
            };
            // 当前缩放 = 初始缩放 + offset × curve(b)。
            if (M.scale) {
                const P = M.scale.offset || 0
                    , Q = M.scale.offsetCurve ? I(M.scale.offsetCurve) : se => se
                    , ae = P * Q(b);
                B.scale = y[O].scale + ae
            }
            // 当前旋转角度（deg）的计算方式与缩放相同。
            if (M.rotate) {
                const P = M.rotate.offset || 0
                    , Q = M.rotate.offsetCurve ? I(M.rotate.offsetCurve) : se => se
                    , ae = P * Q(b);
                B.rotate = y[O].rotate + ae
            }
            // translate.offset 是 [x, y]，两个轴分别乘同一曲线的输出。
            if (M.translate) {
                const P = M.translate.offset || [0, 0]
                    , Q = M.translate.offsetCurve ? I(M.translate.offsetCurve) : ie => ie
                    , ae = P.map(ie => Q(b) * ie)
                    , se = y[O].translate.map( (ie, be) => {
                    var Le;
                    // 位移还会随容器尺寸 v 和本层 initial scale 同比缩放。
                    return (ie + ae[be]) * v * (((Le = M.scale) == null ? void 0 : Le.initial) || 1)
                }
                );
                B.translate = se
            }
            // 将平移、旋转、缩放合并为一次 transform 写入。
            if (Z.style.transform = "translate(".concat(B.translate[0], "px, ").concat(B.translate[1], "px)rotate(").concat(B.rotate, "deg)scale(").concat(B.scale, ")"),
            M.blur) {
                const P = M.blur.offset || 0
                    , Q = M.blur.offsetCurve ? I(M.blur.offsetCurve) : ie => ie
                    , ae = P * Q(b);
                let se = 0;
                // clamp：模糊值下限为 0；alternate：取绝对值，使反向位移也产生正模糊。
                !M.blur.wrap || M.blur.wrap === "clamp" ? se = Math.max(0, y[O].blur + ae) : M.blur.wrap === "alternate" && (se = Math.abs(y[O].blur + ae)),
                // 接近 0 时清空 filter，避免保留无意义的 blur(0px)。
                Z.style.filter = se < 1e-4 ? "" : "blur(".concat(se, "px)")
            }
            if (M.opacity) {
                const P = M.opacity.offset || 0
                    , Q = M.opacity.offsetCurve ? I(M.opacity.offsetCurve) : ie => ie
                    , ae = P * Q(b)
                    , se = y[O].opacity;
                // clamp：把透明度限制在合法的 [0, 1] 区间。
                if (!M.opacity.wrap || M.opacity.wrap === "clamp")
                    Z.style.opacity = Math.max(0, Math.min(1, se + ae)).toString();
                else if (M.opacity.wrap === "alternate") {
                    // alternate：以 2 为周期，让透明度按 0→1→0 往返。
                    const ie = se + ae;
                    let be = Math.abs(ie % 1);
                    Math.abs(ie % 2) >= 1 && (be = 1 - be),
                    Z.style.opacity = be.toString()
                }
            }
        }
        )
    } catch (x) {
        // 任一层渲染失败时记录错误，并通知外部动画状态失效。
        console.error(x),
        i("change", !1)
    }
}
;
// 初始化：将每层第一份资源挂到对应容器；视频立即播放，并请求首帧渲染。
f.map( (x, O) => {
    const M = x.resources[0].el;
    _[O].appendChild(M),
    M.tagName === "VIDEO" && M.play(),
    requestAnimationFrame(R)
}
);
// 在 200ms 内把 b 线性衰减到 0，使背景平滑回到初始位置。
const D = () => {
    const x = performance.now()
        , O = 200
        // 保存回中开始时的位移，后续帧按剩余时间比例计算。
        , M = b;
    cancelAnimationFrame(S);
    const Z = B => {
        B - x < O ? (b = M * (1 - (B - x) / 200),
        R(),
        requestAnimationFrame(Z)) : (b = 0,
        R())
    }
    ;
    S = requestAnimationFrame(Z)
}
;
// 初始时鼠标尚未进入动画有效区域。
l.value = !1,
// time 扩展启用时等待 600ms，给对应扩展/资源留出初始化时间。
(g = r.config.extensions) != null && g.time && await new Promise(x => setTimeout(x, 600)),
// 对外通知动画初始化完成。
i("change", !0);
// 退出动画区域：清除进入状态并启动回中动画。
const H = () => {
    l.value = !1,
    D()
}
    // 鼠标移动处理器。
    , V = x => {
    // 鼠标位于背景容器的页面高度范围内时才计算视差。
    document.documentElement.scrollTop + x.clientY < h ? (l.value || (l.value = !0,
    // 首次进入时记录起点 X；后续位移均相对此点计算。
    L = x.clientX),
    // 像素差除以容器宽度，得到归一化位移 b。
    b = (x.clientX - L) / A,
    // 合并同一刷新周期内的 mousemove，只渲染最新的 b。
    cancelAnimationFrame(S),
    S = requestAnimationFrame(R)) : l.value && (l.value = !1,
    D()),
    // 将事件和位移继续分发给扩展模块。
    u.forEach(O => {
        var M;
        return (M = O.handleMouseMove) == null ? void 0 : M.call(O, {
            e: x,
            displace: b
        })
    }
    )
}
    // resize 处理器：重新计算容器、资源尺寸并强制刷新。
    , j = x => {
    h = w.clientHeight,
    A = w.clientWidth,
    // 资源以高度 155 为设计基准。
    v = h / 155,
    f.forEach(O => {
        O.resources.forEach(M => {
            var Z, B;
            const P = M.el
                // dataset 保存设计尺寸；最终尺寸还需乘 v 和本层 initial scale。
                , Q = Number(P.dataset.width) * v * (((Z = O.scale) == null ? void 0 : Z.initial) || 1)
                , ae = Number(P.dataset.height) * v * (((B = O.scale) == null ? void 0 : B.initial) || 1);
            P.height = ae,
            P.width = Q,
            P.style.height = "".concat(ae, "px"),
            P.style.width = "".concat(Q, "px")
        }
        )
    }
    ),
    cancelAnimationFrame(S),
    // 即使 b 未变，也要按 resize 后的新 v 重算 transform。
    T = NaN,
    S = requestAnimationFrame(R),
    u.forEach(O => {
        var M;
        return (M = O.handleResize) == null ? void 0 : M.call(O, x)
    }
    )
}
;