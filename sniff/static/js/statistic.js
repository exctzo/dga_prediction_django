function showrequests() {
    if (document.getElementById("showreqsButton").style.display == "block"){
        document.getElementById("showreqsButton").style.display = "none";
        document.getElementById("hidereqsButton").style.display = "block";
        elem = document.getElementById("showreqsButton").value;
        document.getElementById(elem).style.display = "block";
    } else {
        document.getElementById("showreqsButton").style.display = "block";
        document.getElementById("hidereqsButton").style.display = "none";
        elem = document.getElementById("hidereqsButton").value;
        document.getElementById(elem).style.display = "none";
        
    }
}
