server {
	#listen   80; ## listen for ipv4; this line is default and implied
	#listen   [::]:80 default ipv6only=on; ## listen for ipv6

	root /var/www/LXC-Web-Panel/static;
	index index.html index.htm;

	server_name fcgi.lxc.example.com;

	access_log /var/log/nginx/fgci.lxc.example.com-access.log;
	error_log /var/log/nginx/fgci.lxc.example.com-error.log warn;

	location = /favicon.ico {
		root /var/www/LXC-Web-Panel/static/ico;
	}

	location ~* \.(css|js|png|ico)$ {
		try_files $uri $uri/ @backend;
	}

	location / {
		include fastcgi_params;
		fastcgi_param PATH_INFO $fastcgi_script_name;
		fastcgi_param SCRIPT_NAME "";
		fastcgi_pass unix:/var/www/LXC-Web-Panel/lwp.sock;
	}

	location @backend {
		internal;
		include fastcgi_params;
		fastcgi_param PATH_INFO $fastcgi_script_name;
		fastcgi_param SCRIPT_NAME "";
		fastcgi_pass unix:/var/www/LXC-Web-Panel/lwp.sock;
#		fastcgi_pass $backend;
	}

	error_page 500 502 503 504 /50x.html;
	location = /50x.html {
		root /usr/share/nginx/www;
	}


	# deny access to .htaccess files, if Apache's document root
	# concurs with nginx's one
	#
	location ~ /\.(ht|git|svn) {
		deny all;
	}
}
