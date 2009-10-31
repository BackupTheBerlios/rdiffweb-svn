function addOnLoadEvent(func)
{
   var oldOnload = window.onload;
   if (typeof(window.onload) !== 'function')
      window.onload = func;
   else
   {
      window.onload = function()
      {
         if (oldOnload)
            oldOnload();
         func();
      }
   }
}

function appendText(elem, text, bold)
{
   if (bold)
      elem = elem.appendChild(document.createElement('B'));
   elem.appendChild(document.createTextNode(text));
}

function showWarning(warningElem, continueBtnText, onContinue)
{
   $('#LightboxContents').empty();
   $('#LightboxContents').append(warningElem);
   $('#LightboxContents').append('<div id="LightboxButtonsContainer"><button type="button" id="ContinueBtn">'+continueBtnText+
                                 '</button>' + '<button type="button" id="CancelBtn">Cancel</button></div>');
   $('#ContinueBtn').click(onContinue);
   $('#CancelBtn').click(Lightbox.hide);
   Lightbox.show();
}

window.Lightbox = {
   init: function()
   {
      makeDivRounded(document.getElementById('LightboxContents'));
   },

   show: function()
   {
      $('#LightboxBackground').show();
      $('#LightboxForeground').show();
   },

   hide: function()
   {
      $('#LightboxBackground').hide();
      $('#LightboxForeground').hide();
   }
};

window.$(Lightbox.init);
