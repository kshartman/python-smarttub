import argparse
import asyncio
import datetime
import logging
from pprint import pprint
import sys

import aiohttp

from . import SmartTub, SpaLight

# Temperature conversion helpers
def fahrenheit(c):
    return round(c * (9.0 / 5.0) + 32, 0)

def fdegrees(c):
    return str(int(fahrenheit(c))) + 'F'

def celsius(f):
    return round((f - 32) * (5.0 / 9.0), 1)

# Light helpers
lightcolornames = ['RED', 'GREEN', 'BLUE', 'WHITE', 'ORANGE', 'PURPLE', 'YELLOW', 'AQUA']

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
                raise Exception('Bad Light Color Commands')
            for l in lcmd[0]:
                if l != exterior_lights or lcmd[1] == 'OFF' or lcmd[1] == 'WHITE':
                    result[l] = lcmd[1]
    return result

def lightmode(lm):
    lm = str(lm).upper()
    if lm == 'RED': return SpaLight.LightMode.RED
    elif lm == 'GREEN': return SpaLight.LightMode.GREEN
    elif lm == 'BLUE': return SpaLight.LightMode.BLUE
    elif lm == 'WHITE': return SpaLight.LightMode.WHITE
    elif lm == 'ORANGE': return SpaLight.LightMode.ORANGE
    elif lm == 'PURPLE': return SpaLight.LightMode.PURPLE
    elif lm == 'YELLOW': return SpaLight.LightMode.YELLOW
    elif lm == 'AQUA': return SpaLight.LightMode.AQUA
    elif lm == 'OFF': return SpaLight.LightMode.OFF
    elif lm == 'MULTI': return SpaLight.LightMode.HIGH_SPEED_COLOR_WHEEL
    elif lm == 'HIGH_SPEED_COLOR_WHEEL': return SpaLight.LightMode.HIGH_SPEED_COLOR_WHEEL
    elif lm == 'HIGH_SPEED_WHEEL': return SpaLight.LightMode.HIGH_SPEED_COLOR_WHEEL
    else:
        raise Exception('Invalid Light Mode')

# Pump helpers
pumpnames = {
    'P1': 'JET1',
    'P2': 'JET2',
    'CP': 'WATERFALL',
    'BLOWER': 'BLOWER',
}

allpumps = ['P1', 'P2', 'CP', 'BLOWER']

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


async def info_command(spas, args):
    for spa in spas:
        print(f"= Spa '{spa.name}' =\n")
        if args.all or args.status or args.location or args.locks:
            status = await spa.get_status_full()

        if args.all or args.status:
            print("== Status ==")
            status_dict = status.properties.copy()
            # redact location for privacy
            location = status_dict.pop("location")
            pprint(status_dict)
            print()

        if args.location:
            # not included in --all
            print(
                f"Location: {location['latitude']} {location['longitude']} (accuracy: {location['accuracy']})\n"
            )

        if args.all or args.pumps:
            print("== Pumps ==")
            for pump in status.pumps:
                print(pump)
            print()

        if args.all or args.lights:
            print("== Lights ==")
            for light in status.lights:
                print(light)
            print()

        if args.all or args.errors:
            print("== Errors ==")
            for error in await spa.get_errors():
                print(error)
            print()

        if args.all or args.reminders:
            print("== Reminders ==")
            for reminder in await spa.get_reminders():
                print(reminder)
            print()

        if args.all or args.locks:
            print("== Locks ==")
            for lock in status.locks.values():
                print(lock)
            print()

        if args.all or args.energy:
            print("== Energy usage ==")
            energy_usage_day = spa.get_energy_usage(
                spa.EnergyUsageInterval.DAY,
                end_date=datetime.date.today(),
                start_date=datetime.date.today() - datetime.timedelta(days=7),
            )
            pprint(await energy_usage_day)
            print()

        if args.all or args.sensors:
            print("== Sensors ==")
            for sensor in status.sensors:
                print(sensor)
            print()

        if args.all or args.debug:
            debug_status = await spa.get_debug_status()
            print("== Debug status ==")
            pprint(debug_status)
            print()


async def set_command(spas, args):
    for spa in spas:
        if args.temperature:
            await spa.set_temperature(args.temperature)

        # Handle pump on/off operations
        if args.turnon or args.turnoff:
            turnon = pumplist(args.turnon) if args.turnon else []
            turnoff = pumplist(args.turnoff) if args.turnoff else []

            pumps = await spa.get_pumps()
            for pump in pumps:
                pump_state = pump.state
                if pump.id in turnon and pump_state == pump.PumpState.OFF:
                    if pump.id != 'CP':
                        await pump.toggle()
                        if args.verbosity > 0:
                            print(f"Turned on {pumpalias(pump.id)}")
                elif pump.id in turnoff and pump_state != pump.PumpState.OFF:
                    if pump.id != 'CP':
                        await pump.toggle()
                        if args.verbosity > 0:
                            print(f"Turned off {pumpalias(pump.id)}")

        # Handle light mode (original upstream syntax)
        if args.light_mode:
            for light in await spa.get_lights():
                if args.verbosity > 0:
                    print(light)
                mode = light.LightMode[args.light_mode]
                if mode == light.LightMode.OFF:
                    await light.set_mode(mode, 0)
                else:
                    await light.set_mode(mode, 50)

        # Handle lights with custom syntax (e.g., "ALL:RED", "SEATS:BLUE")
        if args.lights:
            lights = await spa.get_lights()
            lightops = lightoperations(args.lights)
            for light in lights:
                try:
                    modename = lightops[light.zone]
                    if modename == 'OFF':
                        await light.set_mode(light.LightMode.OFF, 0)
                    else:
                        await light.set_mode(lightmode(modename), 100)
                    if args.verbosity > 0:
                        print(f"Set {lightname(light.zone)} to {modename}")
                except KeyError:
                    # This light zone not specified in the operations
                    pass

        if args.snooze_reminder:
            reminder_id, days = args.snooze_reminder
            days = int(days)
            reminder = next(
                reminder
                for reminder in await spa.get_reminders()
                if reminder.id == reminder_id
            )
            await reminder.snooze(days)

        if args.reset_reminder:
            reminder_id, days = args.reset_reminder
            days = int(days)
            reminder = next(
                reminder
                for reminder in await spa.get_reminders()
                if reminder.id == reminder_id
            )
            await reminder.reset(days)

        if args.lock:
            status = await spa.get_status()
            lock = status.locks[args.lock.lower()]
            await lock.lock()
            print("OK")

        if args.unlock:
            status = await spa.get_status()
            lock = status.locks[args.unlock.lower()]
            await lock.unlock()
            print("OK")


async def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--username", required=True, help="SmartTub account email"
    )
    parser.add_argument(
        "-p", "--password", required=True, help="SmartTub account password"
    )
    parser.add_argument("-v", "--verbosity", action="count", default=0)
    subparsers = parser.add_subparsers()

    info_parser = subparsers.add_parser("info", help="Show information about the spa")
    info_parser.set_defaults(func=info_command)
    info_parser.add_argument(
        "-a", "--all", action="store_true", help="Show all info except location"
    )
    info_parser.add_argument("--spas", action="store_true")
    info_parser.add_argument("--status", action="store_true")
    info_parser.add_argument(
        "--location", action="store_true", help="Show GPS location"
    )
    info_parser.add_argument("--pumps", action="store_true")
    info_parser.add_argument("--lights", action="store_true")
    info_parser.add_argument("--errors", action="store_true")
    info_parser.add_argument("--reminders", action="store_true")
    info_parser.add_argument("--locks", action="store_true")
    info_parser.add_argument("--debug", action="store_true")
    info_parser.add_argument("--sensors", action="store_true")
    info_parser.add_argument("--energy", action="store_true")

    set_parser = subparsers.add_parser("set", help="Change settings on the spa")
    set_parser.set_defaults(func=set_command)
    set_parser.add_argument(
        "-l", "--light_mode", choices=[mode.name for mode in SpaLight.LightMode]
    )
    set_parser.add_argument("-t", "--temperature", type=float)
    set_parser.add_argument(
        "--lights", metavar='NAME:COLOR', nargs='+',
        help='Set light color mode (e.g., ALL:RED, SEATS:BLUE). '
             'Colors: red, green, blue, white, orange, purple, yellow, aqua, multi, off. '
             'Names: seats, footwell, waterfall, exterior, all'
    )
    set_parser.add_argument(
        "--on", metavar='PUMP', dest='turnon', nargs='+',
        help='Turn pumps on. Pumps: P1, P2, CP, BLOWER, JET1, JET2, WATERFALL, or ALL'
    )
    set_parser.add_argument(
        "--off", metavar='PUMP', dest='turnoff', nargs='+',
        help='Turn pumps off. Pumps: P1, P2, CP, BLOWER, JET1, JET2, WATERFALL, or ALL'
    )
    # TODO: should enforce types of str, int
    set_parser.add_argument(
        "--snooze-reminder",
        nargs=2,
        help="Snooze a reminder",
        metavar=("REMINDER_ID", "DAYS"),
    )
    # TODO: should enforce types of str, int
    set_parser.add_argument(
        "--reset-reminder",
        nargs=2,
        help="Reset a reminder",
        metavar=("REMINDER_ID", "DAYS"),
    )
    set_parser.add_argument("--lock", type=str)
    set_parser.add_argument("--unlock", type=str)

    args = parser.parse_args(argv)

    if args.verbosity > 1:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level)

    async with aiohttp.ClientSession() as session:
        st = SmartTub(session)
        await st.login(args.username, args.password)

        account = await st.get_account()

        spas = await account.get_spas()
        await args.func(spas, args)

    # Allow async tasks to complete
    await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
