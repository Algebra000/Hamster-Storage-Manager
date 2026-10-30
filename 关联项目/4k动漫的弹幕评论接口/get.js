(()=> {
        return fetch("https://danmu.v2player.top:8989/cxvbsfhapi.php/barrage/index", {
            method: 'POST',
            body: JSON.stringify({
                vid: 5200,
                sid: 0,
                nid: 1,
            }),
            headers: {
                'accept': '*/*',
                'Content-Type': 'application/json;charset=UTF-8'
            }
        })
            .then(function (res) {
                return res.json()
            })
            .then(function (data) {
                return data.list || []
            })
    })()