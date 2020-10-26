import asyncio
import datetime
import logging
from pprint import pprint
import sys
import argparse

import aiohttp

from . import SmartTub

def fahrenheit(c):
    return round(c * (9.0 / 5.0) + 32, 0)

def fdegrees(c):
    return str(int(fahrenheit(c))) + 'F'

def celsius(f):
    return round((f - 32) * (5.0 / 9.0), 1)

lightcolornames = [ 'RED', 'GREEN', 'BLUE', 'WHITE', 'ORANGE', 'PURPLE', 'YELLOW', 'AQUA' ]

def lightmodename(cs):
    cs = str(cs).upper()
    if (cs == 'HIGH_SPEED_COLOR_WHEEL' or cs == 'HIGH_SPEED_WHEEL' or cs == 'MULTI'):
        return 'MULTI'
    elif (cs == 'OFF' or cs == 'ON'):
        return cs
    elif (cs in lightcolornames):
        return cs
    else:
        return ''
        
lightnames = {
    '1': 'SEATS',
    '2': 'WATERFALL',
    '3': 'FOOTWELL',
    '4': 'EXTERIOR',
}

all_lights = [1, 2, 3, 4]

exterior_lights = 4

def lightname(l):
    if type(l) == int:
        if l >= 1 and l <= 4:
            return lightnames[str(l)]
    l = str(l).upper()
    for key, value in lightnames.items():
        if (key == l or value == l):
            return value
    return ''

def lightnumber(l):
    if type(l) == int:
        return l
    l = str(l).upper()
    for key, value in lightnames.items():
        if (key == l or value == l):
            return int(key)
    return 0
        
def lightoperations(ll):
    result = {}
    if type(ll) == list:
        for s in ll:
            s = str(s).upper()
            lcmd = s.split(':')
            if len(lcmd) == 1:
                lcmd = [all_lights, lcmd[0]]
            elif len(lcmd) == 2:
                if lcmd[0] == 'ALL':
                    lcmd = [all_lights, lcmd[1]]
                else:
                    lcmd = [[lightnumber(lcmd[0])], lcmd[1]]
            else:
                raise('Bad Light Color Commands')
            for l in lcmd[0]:
                if l != exterior_lights or lcmd[1] == 'OFF' or lcmd[1] == 'WHITE':
                    result[l] = lcmd[1]
    return result


def lightmode(lm, light):
    if lm == 'RED': return light.LightMode.RED
    elif lm == 'GREEN': return light.LightMode.GREEN
    elif lm == 'BLUE': return light.LightMode.BLUE
    elif lm == 'WHITE': return light.LightMode.WHITE
    elif lm == 'ORANGE': return light.LightMode.ORANGE
    elif lm == 'PURPLE': return light.LightMode.PURPLE
    elif lm == 'YELLOW': return light.LightMode.YELLOW
    elif lm == 'AQUA': return light.LightMode.AQUA
    elif lm == 'OFF': return light.LightMode.OFF    
    elif lm == 'MULTI': return light.LightMode.HIGH_SPEED_COLOR_WHEEL
    elif lm == 'HIGH_SPEED_COLOR_WHEEL': return light.LightMode.HIGH_SPEED_COLOR_WHEEL
    elif lm == 'HIGH_SPEED_WHEEL': return light.LightMode.HIGH_SPEED_COLOR_WHEEL        
    else:
        raise Exception('Invalid Light Mode')

    
pumpnames = {
    'P1': 'JET1',
    'P2': 'JET2',
    'CP': 'WATERFALL',
    'BLOWER': 'BLOWER',
}


allpumps = [ 'P1', 'P2', 'CP', 'BLOWER' ]


def pumpalias(p):
    p = str(p).upper()
    for key, value in pumpnames.items():
        if (key == p or value == p):
            return value
    return ''


def pumpname(p):
    p = str(p).upper()
    for key, value in pumpnames.items():
        if (key == p or value == p):
            return key
        elif (p == 'ALL'):
            return p
    return ''


def pumplist(pl):
    if (not type(pl) == list):
        return []
    else:
        pl = list(map(pumpname, pl))
        if ('ALL' in pl):
            return allpumps
        else:
            return pl

        
async def main(args):
    async with aiohttp.ClientSession() as session:

        turnon = pumplist(args.turnon)
        turnoff = pumplist(args.turnoff)        

        st = SmartTub(session)
        await st.login(args.username, args.password)
        if (args.verbose or args.debug):
            print('# ---------------------------- ACCOUNT')
        account = await st.get_account()
        if (args.verbose):
            print(account)
        if (args.verbose or args.debug):
            print('# ---------------------------- SPAS')
        spas = await account.get_spas()
        if (args.verbose):
            print(spas)
        spaid = args.spa.upper()
        for spa in spas:
            if (spaid == 'ALL' or spaid == spa.id):
                if (args.verbose or args.debug):
                    print('# ---------------------------- SPA ', spa.id)
                elif (args.summary):
                    print('{:<9} {:<}'.format('SPA:', spa.id))
                status = await spa.get_status()
                if (args.set_temp >= 90.0 and args.set_temp <= 104.0):
                    await st._refresh_token()
                    set_temp = spa.set_temperature(celsius(args.set_temp))
                    await set_temp
                    set_temp = celsius(args.set_temp)
                else:
                    set_temp = status['setTemperature']
                if (not (args.debug or args.summary or args.verbose)) and not turnon and not turnoff and not args.lights:
                    if (args.set_temp or args.get_temp):
                        print(fdegrees(status['water']['temperature']), ' / ', fdegrees(set_temp))
                    return
                if (args.verbose):
                    pprint(status)
                elif (args.summary):
                    print('{:<9} {:<}'.format('ERROR:', status['error']['title']))
                    print('{:<9} {:<} / {:<}'.format('TEMP:', fdegrees(status['water']['temperature']), fdegrees(set_temp)))
                if (args.verbose or args.debug):
                    print('# ---------------------------- PUMPS ')
                pumps = spa.get_pumps()
                for pump in await pumps:
                    pump_state = pump.state
                    if pump.id in turnon and pump_state == 'OFF':
                        if pump.id != 'CP':
                            pump_toggle = pump.toggle()
                            await pump_toggle
                            pump_state = 'ON'
                    elif pump.id in turnoff and pump_state != 'OFF':
                        if pump.id != 'CP':
                            pump_toggle = pump.toggle()
                            await pump_toggle
                            pump_state = 'OFF'
                    if (args.verbose):
                        print(pump)
                    elif (args.summary):
                        print('{:<9} {:<9} - {:<}'.format('PUMP:', pumpalias(pump.id), pump_state))
                if (args.verbose or args.debug):
                    print('# ---------------------------- LIGHTS ')
                lights = spa.get_lights()
                lightops = lightoperations(args.lights)
                for light in await lights:
                    try:
                        modename = lightops[light.zone]
                        if modename == 'OFF':
                            set_mode = light.set_mode(light.LightMode.OFF, 0)
                        else:
                            set_mode = light.set_mode(lightmode(modename, light), 100)
                        await set_mode
                    except KeyError:
                        modename = light.mode
                    if (args.verbose):
                        print(light)
                    elif (args.summary):
                        print('{:<9} {:<9} - {:<}'.format('LIGHT:', lightname(light.zone), lightmodename(modename)))
                if (args.verbose or args.debug):
                    print('# ---------------------------- ERRORS ')
                    errors = await spa.get_errors()
                    if (args.verbose):
                        pprint(errors)
                    print('# ---------------------------- REMINDERS ')
                    reminders = spa.get_reminders()
                    for reminder in await reminders:
                        if (args.verbose):
                            print(reminder)
                    if (args.verbose or args.debug):
                        print('# ---------------------------- DEBUG STATUS ')
                        debug_status = await spa.get_debug_status()
                        if (args.verbose):
                            pprint(debug_status)
                    if (args.verbose or args.debug):
                        print('# ---------------------------- ENERGY USAGE ')
                        energy_usage_day = await spa.get_energy_usage(spa.EnergyUsageInterval.DAY, end_date=datetime.date.today(), start_date=datetime.date.today() - datetime.timedelta(days=7))
                        if (args.verbose):
                            pprint(energy_usage_day)
    await asyncio.sleep(1)
    return
    

class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


parser = argparse.ArgumentParser(prog='smarttub', formatter_class=SmartFormatter, description='\
Hot Tub Control -\n\
PUMPS: P1, P2, CP, BLOWER.\n\
LIGHTS: SEATS, FOOTWELL, WATERFALL, EXTERNAL.')
parser.add_argument('username', help='account user name')
parser.add_argument('password', help='account password')
parser.add_argument('--spa', default='ALL', help='id of spa to manipulate or ALL (default)')
parser.add_argument('--on', metavar='PN', dest='turnon', nargs='+', help='turn pumps on, one or more names or ALL')
parser.add_argument('--off', metavar='PN', dest='turnoff', nargs='+', help='turn pumps off, one or more names or ALL')
parser.add_argument('--set-temp', metavar='F°', type=float, default=0.0, help='set fahrenheit tempeature')
parser.add_argument('--get-temp', action='store_true', help='get fahrenheit tempeature')
parser.add_argument('--status', dest='summary', action='store_true', help='show status of temperature, lights and pumps')
parser.add_argument('--verbose', action='store_true', help='dump json details (implies --status)')
parser.add_argument('--debug', action='store_true', help='show debug trace')
parser.add_argument('--lights', metavar='NAME:COLOR', nargs='+', help='R|\
Set light color mode or turn them off\n\
--lights COLOR will set all lights to color, if supported, else WHITE\n\
COLOR: red, green, blue, white, orange, purple, yellow, aqua, multi, off\n\
NAME: seats, footwell, waterfall, exterior, all\n\
Omitting NAME: and just providing a color is the same as ALL:COLOR\
')

args = parser.parse_args()
if (args.debug):
    logging.basicConfig(level=logging.DEBUG)

if not (args.debug or args.verbose or args.turnon or args.turnoff or args.set_temp or args.get_temp or args.lights):
    args.summary = True

try:
    asyncio.run(main(args))
except:
    print('ERROR:', sys.exc_info()[0])
    sys.exit(1)
else:
    sys.exit(0)

