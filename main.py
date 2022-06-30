import mydialog_api as api
import json

p = api.gen_params(input('Enter your mobile number: '))
if api.get_con_details(p)['success'] == False:
        nic = input('Enter the associated NIC number: ')
        if not api.send_pin(p, nic):
                print('Please retry')
                quit()
        pin = input('Enter the pin received: ')
        if not api.register_with_pin(p, pin):
                print('Please retry')
                quit()
        api.get_con_details(p)
res = api.get_data_usage(p)
print(json.dumps(res, indent=1))
