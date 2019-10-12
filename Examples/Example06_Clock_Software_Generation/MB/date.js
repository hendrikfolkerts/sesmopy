//start the function
date();

function date() {
	var today = new Date();
	var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
	var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
	var curWeekDay = days[today.getDay()];
	var curDay = today.getDate();
	var curMonth = months[today.getMonth()];
	var curYear = today.getFullYear();
	var date = curWeekDay+", "+curYear+" "+curMonth+" "+checkDate(curDay);
	document.getElementById("date").innerHTML = date;
	
	var d = setTimeout(function(){ date() }, 500);
}

function checkDate(i) {
  if (i < 10) {i = "0" + i};
  return i;
}