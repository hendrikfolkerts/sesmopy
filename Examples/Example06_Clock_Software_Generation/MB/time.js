//start the function
time();

function time() {
  var today = new Date();
  var h = today.getHours();
  var m = today.getMinutes();
  var s = today.getSeconds();
  m = checkTime(m);
  s = checkTime(s);
  document.getElementById('time').innerHTML = h + ":" + m + ":" + s;
  var t = setTimeout(time, 500);
}

function checkTime(i) {
  if (i < 10) {i = "0" + i};
  return i;
}