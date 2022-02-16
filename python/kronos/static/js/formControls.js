function showLoading(){
    ignoreTimers = true;
    document.getElementById('queue').innerHTML = '<div class="loader"></div>';
}

function rmField(field_pk){
    //submit post request to remove field from queue, behind the scenes

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "rmField";
    hiddenField.value = field_pk;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function confirmRM(fieldID, field_pk){

    var forReal = confirm("Are you sure you want to remove " + fieldID + " from the queue?")
        if (forReal) {
            showLoading();
            rmField(field_pk);
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
    var forReal = confirm("YOU ARE ABOUT TO DELETE THE QUEUE? \n Are you sure you want to flush the queue?");
    if (forReal) {
        showLoading();
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
    var forReal = confirm("YOU ARE ABOUT TO REPLACE THE QUEUE? \n Are you sure you want to recompute the queue?");
    if (forReal) {
        showLoading();
        redoQueue();
    }
}

function replaceField(field_pk){
    //submit post request to replace field, behind the scenes

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "replace";
    hiddenField.value = field_pk;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function confirmReplace(fieldID, field_pk){

    var forReal = confirm("Would you like to replace field " + fieldID + "?")
        if (forReal) {
            showLoading();
            replaceField(field_pk);
        }
}

function submitBackup(field_pk){
    //submit chosen replacement

    // var ndesigns = 0;
    var prev = 0;
    for (i=0;i<backupFields.length;i++){
        if(backupFields[i].field_pk == field_pk){
            // ndesigns = backupFields[i].designs;
            prev = backupFields[i].prev;
        }
    }

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "backup";
    hiddenField.value = field_pk;
    form.appendChild(hiddenField);

    var hiddenField2 = document.createElement('input');
    hiddenField2.type = 'hidden';
    hiddenField2.name = "prev";
    hiddenField2.value = prev;
    form.appendChild(hiddenField2);

    
    document.body.appendChild(form);
    form.submit();
}

function confirmBackup(fieldID, field_pk){

    var forReal = confirm("Replace with field" + fieldID + "?")
        if (forReal) {
            showLoading();
            submitBackup(field_pk);
        }
}

function redoFromHere(field_pk){
    //reschedule the night after field field_pk

    // var ndesigns = 0;
    var prev = 0;

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "backup";
    hiddenField.value = field_pk;
    form.appendChild(hiddenField);

    var hiddenField2 = document.createElement('input');
    hiddenField2.type = 'hidden';
    hiddenField2.name = "prev";
    hiddenField2.value = prev;
    form.appendChild(hiddenField2);

    var hiddenField3 = document.createElement('input');
    hiddenField3.type = 'hidden';
    hiddenField3.name = "remainder";
    hiddenField3.value = true;
    form.appendChild(hiddenField3);

    
    document.body.appendChild(form);
    form.submit();
}

function confirmRedoFromHere(fieldID, field_pk){

    var forReal = confirm("Reschedule tonight after " + fieldID + "?")
        if (forReal) {
            showLoading();
            redoFromHere(field_pk);
        }
}

function prioritizeField(fieldPk, specialStatus, cadence){
    var form = document.createElement('form');
    form.method = "post";
    form.action = "/fieldQuery.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "prioritizeField";
    hiddenField.value = fieldPk;
    form.appendChild(hiddenField);

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "chosenCadence";
    hiddenField.value = cadence;
    form.appendChild(hiddenField);
    
    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "specialStatus";
    hiddenField.value = specialStatus;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function disableField(fieldPk, specialStatus, cadence){
    var form = document.createElement('form');
    form.method = "post";
    form.action = "/fieldQuery.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "disableField";
    hiddenField.value = fieldPk;
    form.appendChild(hiddenField);
    
    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "chosenCadence";
    hiddenField.value = cadence;
    form.appendChild(hiddenField);
    
    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "specialStatus";
    hiddenField.value = specialStatus;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function resetField(fieldPk, specialStatus, cadence){
    var form = document.createElement('form');
    form.method = "post";
    form.action = "/fieldQuery.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "resetField";
    hiddenField.value = fieldPk;
    form.appendChild(hiddenField);
    
    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "chosenCadence";
    hiddenField.value = cadence;
    form.appendChild(hiddenField);
    
    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "specialStatus";
    hiddenField.value = specialStatus;
    form.appendChild(hiddenField);
    
    document.body.appendChild(form);
    form.submit();
}

function appendDesign(design_id){
    var prev = 0;

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/designDetail.html?designID=" + design_id;

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "append_design_id";
    hiddenField.value = design_id;
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

function confirmAppendDesign(design_id){

    var forReal = confirm("Add " + design_id + " to end of queue?")
        if (forReal) {
            appendDesign(design_id);
        }
}

function insertDesign(design_id, pos){
    var prev = 0;

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/designDetail.html?designID=" + design_id;

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "insert_design_id";
    hiddenField.value = design_id;
    form.appendChild(hiddenField);

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "position";
    hiddenField.value = pos;
    form.appendChild(hiddenField);

    document.body.appendChild(form);
    form.submit();
}

function confirmInsertDesign(design_id, pos){

    let message = "";
    if(pos == 1){
        message = "Insert " + design_id + " to front of queue?";
    }
    else{
        message = "Insert " + design_id + " at " + pos + " in queue?";
    }

    var forReal = confirm(message)
        if (forReal) {
            insertDesign(design_id, pos);
        }
}

function insertWhere(design_id){
    let message = "Insert design " + design_id + " at what position?";
    var pos = parseInt(prompt(message));

    if(isNaN(pos)){
        alert("Invalid input");
    }
    else if(pos < 1){
        alert("Invalid input; pos must be > 0");
    }
    else{
        confirmInsertDesign(design_id, pos);
    }
}
