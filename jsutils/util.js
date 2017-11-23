function encode(str, num)
{
    var arr = [];
    for(var i=0;i<str.length;i++){
        var code = str[i].charCodeAt(0);
        arr.push(String.fromCharCode(code + num));
    }
    return arr.join("");
}
function decode(str, num)
{
    var arr = [];
    for(var i=0;i<str.length;i++){
        var code = str[i].charCodeAt(0);
        arr.push(String.fromCharCode(code - num));
    }
    return arr.join("");
}
