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

function submitBackup(fieldID){
    //submit chosen replacement

    // var ndesigns = 0;
    var prev = 0;
    for (i=0;i<backupFields.length;i++){
        if(backupFields[i].field == fieldID){
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
    hiddenField.value = fieldID;
    form.appendChild(hiddenField);

    var hiddenField2 = document.createElement('input');
    hiddenField2.type = 'hidden';
    hiddenField2.name = "prev";
    hiddenField2.value = prev;
    form.appendChild(hiddenField2);

    
    document.body.appendChild(form);
    form.submit();
}

function confirmBackup(fieldID){

    var forReal = confirm("Replace with field" + fieldID + "?")
        if (forReal) {
            submitBackup(fieldID);
        }
}

function redoFromHere(fieldID){
    //reschedule the night after field fieldID

    // var ndesigns = 0;
    var prev = 0;

    var form = document.createElement('form');
    form.method = "post";
    form.action = "/planObserving.html";

    var hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = "backup";
    hiddenField.value = fieldID;
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

function confirmRedoFromHere(fieldID){

    var forReal = confirm("Reschedule tonight after " + fieldID + "?")
        if (forReal) {
            redoFromHere(fieldID);
        }
}

function prioritizeField(fieldPk, specialStatus, cadence){
    //submit post request to remove field from queue, behind the scenes

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
    //submit post request to remove field from queue, behind the scenes

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
    //submit post request to remove field from queue, behind the scenes

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
