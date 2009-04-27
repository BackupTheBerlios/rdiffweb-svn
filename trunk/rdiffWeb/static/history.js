new function()
{
   $(document).click(function(event) {
      if (event.target.tagName != 'BUTTON' || event.target.type != 'submit')
         return;

      event.preventDefault();
      function submit()
      {
         $('#DeleteDate').val(event.target.value);
         $(event.target).click();
      }
      var warningElem = document.createDocumentFragment();
      appendText(warningElem, 'This will ');
      appendText(warningElem, 'permanently delete', true)
      appendText(warningElem, ' any backups before '+event.target.attributes.date.value+', saving '+
                 event.target.attributes.size.value+' of space. You will not be able '+
                 'to restore from any backup prior to this time!');
      warningElem.appendChild(document.createElement('BR'));
      warningElem.appendChild(document.createElement('BR'));
      appendText(warningElem, 'Are you sure you want to continue?');
      showWarning(warningElem, 'Delete prior backups', submit);
      return false;
   });
};
