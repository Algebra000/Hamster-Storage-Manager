//https://www.ezdmw.org/
//document.querySelector('#player_iframe')
//上面代码返回iframe中的#document存储为全局变量temp1，执行下面代码
//temp1.querySelector('.cmt').nextElementSibling
//返回元素断点“属性修改”，中断后重新运行，即可执行本文件代码
const instances = [];
const visited = new Set();

function search(obj, path) {
if (!obj || typeof obj !== 'object') return;
if (visited.has(obj)) return;
visited.add(obj);

try {
    if (obj.canvas && obj.options && obj.timeline) {
    console.log('找到实例:', obj, '路径:', path);
    instances.push(obj);
    }
    
    Object.getOwnPropertyNames(obj).forEach(prop => {
    try {
        const val = obj[prop];
        if (val && typeof val === 'object') {
        search(val, path + '.' + prop);
        }
    } catch (e) {}
    });
} catch (e) {}
}

search(window, 'window');
//console.log(`共找到 ${instances.length} 个 t 实例`);

if (instances.length>0)
{
    let str = '[\n';
    for(let i = 0;i<instances[0].timeline.length;i++)
    {
        str += '\t{\n\t\t"time": ' + String((instances[0].timeline[i].stime)/1000) + ',\n\t\t"text": "';
        let open = true;  // 标记下一个是左引号还是右引号
        let contentstr = instances[0].timeline[i].text;
        contentstr = contentstr.replace(/\\/g, '＼');
        contentstr = contentstr.replace(/"/g, function() {
            open = !open;  // 每遇到一个引号就切换状态
            return open ? '”' : '“';  // 先遇到的是左引号，所以open初始为true，第一次替换后变成false返回右引号
        });
        str += contentstr + '",\n\t\t"type": ';
        if (instances[0].timeline[i].mode == 1)
        {
            str += '"scroll",\n\t\t"color": ';
        }
        else
        {
            str += '"top",\n\t\t"color": '
        }
        let color = Math.floor(instances[0].timeline[i].color) & 0xFFFFFF;
        let hex = color.toString(16).padStart(6, '0').toUpperCase();
        str += '"' + `#${hex}` + '",\n\t\t"dmid": "' + instances[0].timeline[i].dbid + '",\n\t\t"send-time": ' + String(instances[0].timeline[i].date) + ',\n\t\t"src":"E站"\n\t}';
        if (i!=instances[0].timeline.length-1)
        {
            str += ',\n';
        }

    }
    str += ']'
    console.log(str);
}


