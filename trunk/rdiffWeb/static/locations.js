new function()
{
   $(document).click(function(event) {
      if (event.target.tagName != 'BUTTON' || event.target.type != 'submit')
         return;

      event.preventDefault();
      function submit()
      {
         $(event.target).click();
      }

      var repo = $(event.target).siblings('input[type=hidden]')[0].value;
      var warningElem = document.createDocumentFragment();
      appendText(warningElem, 'You are about to ');
      appendText(warningElem, 'permanently delete', true)
      appendText(warningElem, ' the "'+repo+'" backup location. Any data contained within this backup will be ');
      appendText(warningElem, 'irretrievably lost!', true);
      warningElem.appendChild(document.createElement('BR'));
      warningElem.appendChild(document.createElement('BR'));
      appendText(warningElem, 'Are you sure you want to continue?');
      showWarning(warningElem, 'Delete this backup', submit);
      return false;
   });
};
