mt940 parsig
	parse
	dump to dsv
	merge dsv
membership fees
	find for user
		allow alternate regexp per user on not matching transactions
	calculate fees
	allow resetting fees
	bussines rules
		prevent hoarding
		minimal value
	print dsv with results
	send notifications (emacsem przez sendmail)
user management
	add
	remove
	show
	modify
		usernme
		email
		alternate regexp
hooks
	@user creation
	@user drop

struktura: user
user: id;login;email;data_przystapienia;imie nazwisko;adres;rola

struktura: event
data;user id;event [args]

