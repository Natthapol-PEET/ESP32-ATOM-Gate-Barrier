dat_file = "wifi.dat"

# with open(dat_file, 'r') as file:
#     text = file.read()
#     print(text)

with open(dat_file, 'r') as f:
    lines = f.readlines()
profiles = {}
for line in lines:
    ssid, password = line.strip("\n").split(";")
profiles[ssid] = password

print(profiles)