
function onNotifyTypeChange()
{
   $('INPUT[name=NotifyType]').each(function(index, elem) {
      var enabled = elem.checked;

      var parentDiv = $(elem).closest('.NotifyGrouping');
      if (enabled)
         parentDiv.removeClass('Disabled');
      else
         parentDiv.addClass('Disabled');

      // Disable all child selects
      parentDiv.find('SELECT').each(function(index, select){
         select.disabled = !enabled;
      });
   });
}

$(document).ready(function() {
   $('INPUT[name=NotifyType]').change(function(event) {
      onNotifyTypeChange();
   });
   onNotifyTypeChange();
});
