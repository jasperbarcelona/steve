$(document).ready(function(){
  
$(window).load(function(){
  initialize_page();
  setTimeout(function() {
    $('#mainPreloader').fadeOut();
  }, 3000);
});

$('#modalLoader').hide();
$('#contentLoader').hide();
$('#settingsContentLoader').hide();

$('.form-control.floatlabel').floatlabel({
    labelEndTop:'-2px'
});

$(".datepicker").datepicker({
    dateFormat: "MM dd, yy"
});

$('.clockpicker').clockpicker({
    twelvehour: true,
    donetext: 'Done',
    autoclose: false
});

$('.tooltip').tooltipster({
   animation: 'grow',
   delay: 200,
   theme: 'tooltipster-shadow',
   trigger: 'hover'
});

$('.active-entry-right').on('click', function () {
  $('.active-entry-action-container').removeClass('visible');
  $(this).find('.active-entry-action-container').addClass('visible');
});

$('.sort-selector').on('click', function () {
  $('.sort-selector').removeClass('active');
  $(this).addClass('active');
  $('#saveSortBtn').attr('disabled', false);
});

$('#clearActiveSearchBtn').on('click', function () {
  $('#searchActive').val('');
  search_active_transactions('');
});

$('#clearHistorySearchBtn').on('click', function () {
  $('#searchHistory').val('');
  search_history('');
});


$('#closeReplyError').on('click', function () {
  $('#ErrorSnackbar').fadeOut();
});

$('#closeReplySuccess').on('click', function () {
  $('#successSnackbar').fadeOut();
});

$('.close-action-icon').on('click', function (e) {
  e.stopPropagation();
  button_id = $(this).attr('data-button-id');
  $('#'+button_id).button('complete');
  $('.active-entry-action-container').removeClass('visible');
});

$('.fixed-action-btn').floatingActionButton();

$('.service-quantity-text').on('keyup', function () {
  quantity = $(this).val();
  if (quantity == '') {
    quantity = 0;
    $(this).val(quantity);
    $(this).select();
  }
  get_current_total();
});

$('#additionalCharge').on('keyup', function () {
  quantity = $(this).val();
  if (quantity == '') {
    quantity = 0;
    $(this).val(quantity);
    $(this).select();
  }
  get_current_total();
});

$('#addTransactionModal .form-control').on('keyup', function () {
  customer_name = $('#addTransactionName').val();
  customer_msisdn = $('#addTransactionMsisdn').val();
  total = $('#transactionTotal').html();

  if ((customer_name != '') && (total != 'PHP 0.00')) {
    $('#saveTransactionBtn').attr('disabled', false);
  }
  else {
    $('#saveTransactionBtn').attr('disabled', true);
  }
});

$('#addServiceModal .form-control').on('keyup', function () {
  service_name = $('#addServiceName').val();
  service_price = $('#addServicePrice').val();

  if ((service_name != '') && (service_price != '')) {
    $('#saveServiceBtn').attr('disabled', false);
  }
  else {
    $('#saveServiceBtn').attr('disabled', true);
  }
});

$('#addTransactionModal .form-control').on('change', function () {
  customer_name = $('#addTransactionName').val();
  customer_msisdn = $('#addTransactionMsisdn').val();
  total = $('#transactionTotal').html();

  if ((customer_name != '') && (total != 'PHP 0.00')) {
    $('#saveTransactionBtn').attr('disabled', false);
  }
  else {
    $('#saveTransactionBtn').attr('disabled', true);
  }
});

$('#addTransactionModal').on('hidden.bs.modal', function () {
  $('#addTransactionModal .error-icon-container').addClass('hidden');
  $('#addTransactionName').val('');
  $('#addTransactionMsisdn').val('');
  $('#addTransactionModal .service-quantity-text').val('0');
  $('#addTransactionModal .form-control').change();
  $('#addTransactionName').css('border','1px solid #ccc');
  $('#addTransactionMsisdn').css('border','1px solid #ccc');
  $('#saveTransactionBtn').button('complete');
  $('#transactionTotal').html('PHP 0.00');
  setTimeout(function() {
    $('#saveTransactionBtn').attr('disabled', true);
  }, 500);
});

$('#addUserModal').on('hidden.bs.modal', function () {
  $('#addUserRole').prop('selectedIndex',0);
  $('#addUserModal .form-control').val('');
  $('#addUserModal .form-control').change();
  $('#addUserModal .error-icon-container').addClass('hidden');
  $('#addUserModal .form-control').css('border','1px solid #ccc');
  $('#saveUserBtn').button('complete');
  setTimeout(function() {
    $('#saveUserBtn').attr('disabled', true);
  }, 500);
});

$('#addServiceModal').on('hidden.bs.modal', function () {
  $('#addServiceModal .error-icon-container').addClass('hidden');
  $('#addServiceName').val('');
  $('#addServicePrice').val('');
  $('#addServiceModal .form-control').change();
  $('#addServiceName').css('border','1px solid #ccc');
  $('#addServicePrice').css('border','1px solid #ccc');
  $('#saveServiceBtn').button('complete');
  setTimeout(function() {
    $('#saveServiceBtn').attr('disabled', true);
  }, 500);
});

$('#serviceInfoModal').on('hidden.bs.modal', function () {
  $('#serviceInfoModal .error-icon-container').addClass('hidden');
  $('#editServiceName').val('');
  $('#editServicePrice').val('');
  $('#serviceInfoModal .form-control').change();
  $('#editServiceName').css('border','1px solid #ccc');
  $('#editServicePrice').css('border','1px solid #ccc');
  $('#editServiceBtn').button('complete');
  setTimeout(function() {
    $('#editServiceBtn').attr('disabled', true);
  }, 500);
});

$('#transactionInfoModal').on('hidden.bs.modal', function () {
  $('#modalLoader').hide();
});

$('#addTransactionModal').on('shown.bs.modal', function () {
  $('#addTransactionName').focus();
});

$('#addServiceModal').on('shown.bs.modal', function () {
  $('#addServiceName').focus();
});

$('.typeahead').on('typeahead:selected', function(evt, item) {
  
});

});

$('#addUserModal .form-control').on('keyup', function () {
  name = $('#addUserName').val();
  email = $('#addUserEmail').val();
  temp_pw = $('#addUserPassword').val();
  role = $('#addUserRole').val();

  if ((name != '') && (email != '') && (temp_pw != '')) {
    $('#saveUserBtn').attr('disabled',false);
  }
  else {
    $('#saveUserBtn').attr('disabled',true);
  }
});

$('#addUserModal .form-control').on('change', function () {
  name = $('#addUserName').val();
  email = $('#addUserEmail').val();
  temp_pw = $('#addUserPassword').val();
  role = $('#addUserRole').val();

  if ((name != '') && (email != '') && (temp_pw != '')) {
    $('#saveUserBtn').attr('disabled',false);
  }
  else {
    $('#saveUserBtn').attr('disabled',true);
  }
});

$('#addUserModal').on('shown.bs.modal', function () {
    $('#addUserName').focus();
});

$('#resetPasswordModal').on('hidden.bs.modal', function () {
  $('#resetPasswordModal .form-control').val('');
  $('#resetPasswordModal .form-control').change();
  $('#resetPasswordModal .error-icon-container').addClass('hidden');
  $('#resetPasswordModal .form-control').css('border','1px solid #ccc');
});

$('#resetPasswordModal .form-control').on('keyup', function () {
  temp_pw = $('#resetPasswordText').val();
  temp_pw_confirm = $('#resetPasswordConfirmText').val();
  role = $('#addUserRole').val();

  if ((temp_pw != '') && (temp_pw_confirm != '') && (temp_pw.length >= 8) && (temp_pw_confirm.length >= 8) && (temp_pw_confirm == temp_pw)) {
    $('#resetPasswordBtn').attr('disabled',false);
  }
  else {
    $('#resetPasswordBtn').attr('disabled',true);
  }
});

$('#resetUserPasswordModal .form-control').on('keyup', function () {
  temp_pw = $('#resetUserPasswordText').val();
  temp_pw_confirm = $('#resetUserPasswordConfirmText').val();
  role = $('#addUserRole').val();

  if ((temp_pw != '') && (temp_pw_confirm != '') && (temp_pw.length >= 8) && (temp_pw_confirm.length >= 8) && (temp_pw_confirm == temp_pw)) {
    $('#resetUserPasswordBtn').attr('disabled',false);
  }
  else {
    $('#resetUserPasswordBtn').attr('disabled',true);
  }
});

$('#changePasswordModal').on('shown.bs.modal', function () {
    $('#changePasswordText').focus();
});

$('#changePasswordModal .form-control').keyup(function(e){
  password = $('#changePasswordText').val();
  password_confirm = $('#changePasswordConfirmText').val();

  if ((password != '') && (password_confirm != '') && (password == password_confirm)) {
    $('#savePasswordBtn').attr('disabled',false);
  }
  else {
    $('#savePasswordBtn').attr('disabled',true);
  }
});

(function($) {
$.fn.donetyping = function(callback){
    var _this = $(this);
    var x_timer;    
    _this.keyup(function (){
        clearTimeout(x_timer);
        x_timer = setTimeout(clear_timer, 500);
    }); 

    function clear_timer(){
        clearTimeout(x_timer);
        callback.call(_this);
    }
}
})(jQuery);

$('#searchActive').donetyping(function(callback){
  search_active_transactions($(this).val());
});

$('#searchHistory').donetyping(function(callback){
  search_history($(this).val());
});