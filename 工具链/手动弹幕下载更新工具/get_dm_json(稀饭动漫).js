//document.querySelector('iframe[mozallowfullscreen="mozallowfullscreen"]')
//class="ec-danMa text dm-show"
let str = '[\n';
for(let i = 0;i<this.dan.length;i++)
{
    str += '\t{\n\t\t"time": ' + String(this.dan[i].time) + ',\n\t\t"text": "';
    let open = true;  // 标记下一个是左引号还是右引号
    let contentstr = this.dan[i].text;
    contentstr = contentstr.replace(/\\/g, '＼');
    contentstr = contentstr.replace(/"/g, function() {
        open = !open;  // 每遇到一个引号就切换状态
        return open ? '”' : '“';  // 先遇到的是左引号，所以open初始为true，第一次替换后变成false返回右引号
    });
    str += contentstr + '",\n\t\t"type": ';
    if (this.dan[i].type == 'right')
    {
        str += '"scroll",\n\t\t"color": ';
    }
    else
    {
        str += '"top",\n\t\t"color": '
    }
    str += '"' + this.dan[i].color + '",\n\t\t"src":"稀饭动漫"\n\t}';
    if (i!=this.dan.length-1)
    {
        str += ',\n';
    }

}
str += ']'
console.log(str);


