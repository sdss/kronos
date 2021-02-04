function rmField(fieldID){
    //submit post request to remove field from queue, behind the scenes

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "rmField";
    hiddenField.value = fieldID;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function confirmRM(fieldID){

    var forReal = confirm("Are you sure you want to remove " + fieldID + " from the queue?")
        if (forReal) {
            rmField(fieldID);
        }
}