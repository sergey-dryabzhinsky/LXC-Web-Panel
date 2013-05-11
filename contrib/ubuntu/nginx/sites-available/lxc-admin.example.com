server {
	#listen   80; ## listen for ipv4; this line is default and implied
	#listen   [::]:80 default ipv6only=on; ## listen for ipv6

	root /var/www/Lxc-Web-Panel/static;
	index index.html index.htm;

	server_name lxc-admin.example.com;

	set $backend http://127.0.1.2:5000;

	location / {
		try_files $uri $uri/ @backend;
	}

	location @backend {
		internal;
		proxy_pass $backend;
		include proxy_params;
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
