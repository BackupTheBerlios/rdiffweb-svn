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
new function()
{
   $(Lightbox.init);
};
