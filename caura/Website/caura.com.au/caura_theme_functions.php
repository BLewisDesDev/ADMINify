<?php
/**
 * Caura Theme functions and definitions
 *
 * @link https://developer.wordpress.org/themes/basics/theme-functions/
 *
 * @package Caura
 * @since 1.0.0
 */

/**
 * Define Constants
 */
define( 'CHILD_THEME_CAURA_VERSION', '1.0.0' );

/**
 * Enqueue styles
 */
function child_enqueue_styles() {

	wp_enqueue_style( 'caura-theme-css', get_stylesheet_directory_uri() . '/style.css', array('astra-theme-css'), CHILD_THEME_CAURA_VERSION, 'all' );

}

add_action( 'wp_enqueue_scripts', 'child_enqueue_styles', 15 );

add_filter( 'gform_phone_formats', 'au_phone_format' );
function au_phone_format( $phone_formats ) {
    $phone_formats['au'] = array(
        'label'       => 'Australia',
        'mask'        => '9999999999',
        'regex'       => '/^\({0,1}((0|\+61)(2|4|3|7|8)){0,1}\){0,1}(\ |-){0,1}[0-9]{2}(\ |-){0,1}[0-9]{2}(\ |-){0,1}[0-9]{1}(\ |-){0,1}[0-9]{3}$/',
        'instruction' => 'Australian phone numbers.',
    );
 
    return $phone_formats;
}

add_filter( 'wp_sitemaps_enabled', '__return_true' );

//prevent Users
add_filter( 'wp_sitemaps_add_provider', function ($provider, $name) {
  return ( $name == 'users' ) ? false : $provider;
}, 10, 2);

//remove images label on hover
add_filter( 'wp_get_attachment_image_attributes', 'remove_image_text');
function remove_image_text( $attr ) {
unset($attr['title']);
return $attr;
}



add_action('wp_body_open', 'add_code_on_body_open');
function add_code_on_body_open() {
    echo '<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PZXPD5SR"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->';
}



add_filter( 'lostpassword_url', 'mmw_lost_password_page', 10, 2 );
function mmw_lost_password_page( $lostpassword_url ) {
    return home_url( '/caura-login.php?action=lostpassword');   // The name of your new login file
}

add_filter('logout_url', 'mmw_modify_logout_url', 10, 2);
function mmw_modify_logout_url($logout_url, $redirect) {
        $logout_url = str_replace('wp-login.php', 'caura-login.php', $logout_url);
    return $logout_url;
}


function mmw_custom_login_url($login_url, $redirect, $force_reauth) {
	$login_url = home_url('/caura-login');
	if(!empty($redirect)){
		$login_url = add_query_arg( 'redirect_to', $redirect, $login_url );
	}
    return $login_url;
}
add_filter('login_url', 'mmw_custom_login_url', 10, 3);

function mmw_redirect_to_custom_login() {
    if ((strpos($_SERVER['REQUEST_URI'], 'wp-admin') !== false || strpos($_SERVER['REQUEST_URI'], 'wp-login.php') !== false) && !is_user_logged_in()) {
        wp_redirect(home_url('/404'));
        exit();
    }
}
add_action('init', 'mmw_redirect_to_custom_login');




