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

function flushQueue(){
    //submit post request to remove field from queue, behind the scenes

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "flush";
    hiddenField.value = true;
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

function confirmFlush(){
    var forReal = confirm("Are you sure you want to flush the queue?");
    if (forReal) {
        flushQueue();
    }
}

function redoQueue(){
    //submit post request to remove field from queue, behind the scenes

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "redo";
    hiddenField.value = true;
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

function confirmRedo(){
    var forReal = confirm("Are you sure you want to recompute the queue?");
    if (forReal) {
        redoQueue();
    }
}

function replaceField(fieldID){
    //submit post request to replace field, behind the scenes

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "replace";
    hiddenField.value = fieldID;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function confirmReplace(fieldID){

    var forReal = confirm("Would you like to replace field " + fieldID + "?")
        if (forReal) {
            replaceField(fieldID);
        }
}
