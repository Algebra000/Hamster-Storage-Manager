//document.querySelector(".bpx-player-render-dm-wrap")

let str = '[\n';
for(let i = 0;i<this.manager.dataBase.dmArray.length;i++)
{
    str += '\t{\n\t\t"time": ' + String(this.manager.dataBase.dmArray[i].stime) + ',\n\t\t"text": "';
    let open = true;  // 标记下一个是左引号还是右引号
    let contentstr = this.manager.dataBase.dmArray[i].text;
    contentstr = contentstr.replace(/\\/g, '＼');
    contentstr = contentstr.replace(/"/g, function() {
        open = !open;  // 每遇到一个引号就切换状态
        return open ? '”' : '“';  // 先遇到的是左引号，所以open初始为true，第一次替换后变成false返回右引号
    });
    str += contentstr + '",\n\t\t"type": ';
    if (this.manager.dataBase.dmArray[i].mode == 1)
    {
        str += '"scroll",\n\t\t"color": ';
    }
    else
    {
        str += '"top",\n\t\t"color": '
    }
    let color = Math.floor(this.manager.dataBase.dmArray[i].color) & 0xFFFFFF;
    let hex = color.toString(16).padStart(6, '0').toUpperCase();
    let colorfulstr = "false";
    if (this.manager.dataBase.dmArray[i].colorful!=0){colorfulstr = "true";}
    str += '"' + `#${hex}` + '",\n\t\t"dmid": "' + this.manager.dataBase.dmArray[i].dmid
     + '",\n\t\t"send-time": ' + String(this.manager.dataBase.dmArray[i].date) 
     + ',\n\t\t"is-colorful": ' + colorfulstr 
     + ',\n\t\t"font-size": ' + String(this.manager.dataBase.dmArray[i].size)
     + ',\n\t\t"weight": ' + String(this.manager.dataBase.dmArray[i].weight)
     +',\n\t\t"src": "B站"\n\t}';
    if (i!=this.manager.dataBase.dmArray.length-1)
    {
        str += ',\n';
    }

}
str += ']'
console.log(str);


