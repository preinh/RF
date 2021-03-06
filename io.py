# by TR

from obspy import readEvents
from obspy.core.event import (Catalog, Event, CreationInfo, EventDescription,
                              Origin, Magnitude)
from obspy.core.util import AttribDict
from rf import conf
import os
import pickle

CONF_ABBREVS = {'{net}':'{stats.network}',
                '{sta}':'{stats.station}',
                '{loc}':'{stats.location}',
                '{cha}':'{stats.channel}'}

conf.rf_data_in = conf.rf_data
conf.mout_data_in = conf.rf_data
for key, val in CONF_ABBREVS.items():
    conf.dmt_data = conf.dmt_data.replace(key, '*')
    conf.rf_data_in = conf.rf_data_in.replace(key, '*')  #@UndefinedVariable
    conf.mout_data_in = conf.mout_data_in.replace(key, '*')  #@UndefinedVariable
    conf.rf_data = conf.rf_data.replace(key, val)
    conf.mout_data = conf.mout_data.replace(key, val)
    conf.sum_data = conf.sum_data.replace(key, val)

def create_dir(filename):
    """
    Create directory of filname if it does not exist.
    """
    head = os.path.dirname(filename)
    if head != '' and not os.path.isdir(head):
        os.makedirs(head)

def read_stations(fname):
    """
    Read station positions from whitespace delimited file
    
    Example file:
    # station  lat  lon  elev
    STN  10.0  -50.0  160
    """
    ret = AttribDict()
    with open(fname) as f:
        for line in f.readlines():
            if not line[0].startswith('#'):
                vals = line.split()
                ret[vals[0]] = AttribDict()
                ret[vals[0]].latitude = float(vals[1])
                ret[vals[0]].longitude = float(vals[2])
                ret[vals[0]].elevation = float(vals[3])
    return ret

def write_stations(fname, dic, comment='# station  lat  lon  elev\n'):
    """
    Write dictionary of station positions to file
    """
    with open(fname, "w") as f:
        f.write(comment)
        for key, val in sorted(dic.items()):
            f.write('%s  %s  %s  %s\n' % (key, val['latitude'],
                                          val['longitude'], val['elevation']))

def read_sac_header(stream):
    for tr in stream:
        tr.stats.latitude = tr.stats.sac.stla
        tr.stats.longitude = tr.stats.sac.stlo
        tr.stats.elevation = tr.stats.sac.stel

def write_sac_header(stream, event=None):
    for tr in stream:
        try:
            tr.stats.sac.stla = tr.stats.latitude
        except KeyError:
            tr.stats.sac = AttribDict({})
            tr.stats.sac.stla = tr.stats.latitude
        tr.stats.sac.stlo = tr.stats.longitude
        tr.stats.sac.stel = tr.stats.elevation
        if event:
            tr.stats.sac.evla = event.origins[0].latitude
            tr.stats.sac.evlo = event.origins[0].longitude
            tr.stats.sac.evdp = event.origins[0].depth

def set_paths(dmt_path, output_path=None):
    if not output_path:
        output_path = dmt_path
    conf.dmt_path = os.path.expanduser(dmt_path)
    conf.output_path = os.path.expanduser(output_path)

def convert_dmteventfile():
    eventsfile1 = os.path.join(conf.dmt_path, 'EVENT', 'event_list')
    eventsfile2 = os.path.join(conf.dmt_path, 'EVENT', 'events.xml')
    with open(eventsfile1) as f:
        events1 = pickle.load(f)
    events2 = Catalog()
    for ev in events1:
        orkw = {'time': ev['datetime'],
                'latitude': ev['latitude'],
                'longitude': ev['longitude'],
                'depth': ev['depth']}
        magkw = {'mag': ev['magnitude'],
                 'magnitude_type': ev['magnitude_type']}
        evdesargs = (ev['flynn_region'], 'Flinn-Engdahl region')
        evkw = {'resource_id': ev['event_id'],
                'event_type': 'earthquake',
                'creation_info': CreationInfo(author=ev['author']),
                'event_descriptions': [EventDescription(*evdesargs)],
                'origins': [Origin(**orkw)],
                'magnitudes': [Magnitude(**magkw)]}
        events2.append(Event(**evkw))
    events2.write(eventsfile2, 'QUAKEML')

def read_rfevents(events):
    if isinstance(events, basestring):
        if not os.path.exists(events):
            events = os.path.join(conf.output_path, 'EVENT', events)
        events = readEvents(events)
    return events

def create_rfeventsfile(events='events.xml',
                        eventsfile='events_rf.xml', filters=None):

    if isinstance(events, basestring):
        if not os.path.exists(events):
            events = os.path.join(conf.dmt_path, 'EVENT', 'events.xml')
        events = readEvents(events)
    if filters:
        events.filter(*filters)
    eventsfile = os.path.join(conf.output_path, 'EVENT', eventsfile)
    create_dir(eventsfile)
    events.write(eventsfile, 'QUAKEML')
