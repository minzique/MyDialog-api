import mydialog_api as api
import json

#FIXME add error handling instead of quit() lol	
def register(p):
	nic = input('Enter the associated NIC number: ')
	if not api.send_pin(p, nic):
		print('Please retry')
		quit()
	pin = input('Enter the pin received: ')
	if not api.register_with_pin(p, pin):
		print('Please retry')
		quit()   
   
def print_balance(con):
	data = con['data']['status']['ocs']['payment']
	print(f'Connection: {data["mode"]}')
	if data['mode'] != 'POSTPAID':
		print(f'Outstanding: {data["outstanding"]}') 
	print(f'Balance: {data["balance"]}')
	
def print_data_usage(data):
	data = data['data']['detailData']
	for x in data:
		print(f'{x["title"]}:')
		for y in x['packUsageData']:
			print(f'\tPackage: {y["packageName"]}')
			if y['packageTotal']: 
				print(f'\tTotal: {y["packageTotal"]}')
			print(f'\tRemaining: {y["balance"]}')
			print(f'\tValidity: {y["validity"]}\n')
		print('')
  
def main():
	p = api.gen_params(input('Enter your mobile number: '))
	con = api.get_con_details(p)
	if con['success'] == False:
		register(p)
		con = api.get_con_details(p)
	print_balance(con)
	data = api.get_data_usage(p)
	if not 'detailData' in data['data']: 
		quit()
	print_data_usage(data)

if __name__ == '__main__':
    main()