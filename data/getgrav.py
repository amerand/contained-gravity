import numpy as np

from astropy.io import fits
from astropy.utils.iers import conf
from astropy.time import Time
import astropy.time

conf.auto_max_age = None

import astroquery
from astroquery.eso import Eso, Conf
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
from astropy import units as u

import pickle
import time 

eso = Eso()
eso.ROW_LIMIT = 5000
eso.QUERY_INSTRUMENT_URL = 'http://archive.eso.org/wdb/wdb/eso'

def getP2vm(starttime, spec='HIGH', pola='COMBINED', delta_day=0, onlyOne=True):
    """
    starttime is the date of the start of the night, e.g. '2020-01-01T00:00:00'
    """
    start = Time(int(Time(starttime).mjd)+0.8  + delta_day, format='mjd').isot
    end = Time(int(Time(starttime).mjd)+1.8 + delta_day , format='mjd').isot
    col_filter={'stime':start, 'etime':end}
    night = eso.query_instrument('gravity', column_filters=col_filter, dp_cat='CALIB')
    w = (night['INS.SPEC.RES']==spec)*(night['INS.POLA.MODE']==pola)
    if any(w*(night['DPR.TYPE']=='WAVE')):
        dit = night[w*(night['DPR.TYPE']=='WAVE')]['DET2.SEQ1.DIT'][0]
    else:
        # -- no P2VM!
        return []
    w *= night['DET2.SEQ1.DIT']==dit
    w *= np.array([typ in ['DARK', 'FLAT', 'WAVE', 'WAVE,SC', 'P2VM'] for typ in night['DPR.TYPE']])
    expected = np.array(['DARK', 'FLAT', 'FLAT', 'FLAT', 'FLAT', 'WAVE,SC', 'WAVE', 'P2VM',
                      'P2VM', 'P2VM', 'P2VM', 'P2VM', 'P2VM'])
    if onlyOne and all(night[w][:13]['DPR.TYPE']==expected):
        return night[w][:13]
    else:
        return night[w]

def getDark(starttime, spec='HIGH', pola='COMBINED', dit=30, delta_day=0):
    """
    starttime is the date of the start of the night, e.g. '2020-01-01T00:00:00'
    """
    start = Time(int(Time(starttime).mjd)+0.8  + delta_day, format='mjd').isot
    end = Time(int(Time(starttime).mjd)+1.8 + delta_day , format='mjd').isot
    col_filter={'stime':start, 'etime':end}
    night = eso.query_instrument('gravity', column_filters=col_filter, dp_cat='CALIB')
    w = (night['INS.SPEC.RES']==spec)*(night['INS.POLA.MODE']==pola)*(night['DET2.SEQ1.DIT']==dit)*(night['DPR.TYPE']=='DARK')
    return night[w]

def getTargetNight(target, starttime, dist_target=10/3600, dist_calib=20, calibValidity=5, verbose=False, withP2vm=True):
    """
    Get all GRAVITY data DP.IDs for target "target" (e.g. "eta Car") for night with start date "starttime" (e.g. "2020-05-30"). 
    The script also finds associated calibrations (CAL star, P2VM and DARKS):
    * calibrator stars are selected with same mode and DIT, whithin "dist_calib" degrees (default 20)
    * daytime calibration within "calibValidity" days
    
    The data are obtained by selecting by coordinates, based on the SIMBAD coordinates and distance tolerance of "dist_target" 
    degrees (default 10").
    """
    if not 'T' in starttime:
        starttime += 'T00:00:00'
    start = Time(int(Time(starttime).mjd)+0.8  , format='mjd').isot
    end = Time(int(Time(starttime).mjd)+1.8  , format='mjd').isot
    col_filter = {'stime':start, 'etime':end}
    night = eso.query_instrument('gravity', column_filters=col_filter)
    
    s = Simbad.query_object(target)
    c = SkyCoord(s['RA'][0]+' '+s['DEC'][0], unit=(u.hourangle, u.deg))
    ra, dec = c.ra.value, c.dec.value
    
    # -- distance to the object of interest
    night['dist'] = np.round(np.sqrt((night['DEC']-dec)**2 +  np.cos(dec*np.pi/180)**2*(night['RA']-ra)**2), 1)
    # -- check OBs within 1 degree of our object of interest
    w = night['dist']<dist_target
    
    if not any(w):
        print('Warning, no observations found whithin %.2f deg of %s'%(dist_target, target))
        print('  ', set(night[night['DPR.CATG']=='SCIENCE']['OBS.TARG.NAME']))
        return []
    print('[%d/%d OBs withing %.1f"]'%(np.sum(w), len(night['dist']), dist_target*3600))
    # -- get all the mode+DIT for the observation of the object during the night
    modes = list(set(zip(night['INS.SPEC.RES'][w], night['INS.POLA.MODE'][w], night['DET2.SEQ1.DIT'][w])))

    # -- correct mode and close in sky to the interesting object
    dpid = []
    # -- range of days for with the calibrations are valid
    # [0, -1, 1, -2, 2, ... -calibValidity, calibValidity]
    dt = [i*(-1)**(i%2)//2 for i in range(2*calibValidity+1)]
    for m in modes:
        w = (night['INS.SPEC.RES']==m[0])*(night['INS.POLA.MODE']==m[1])*(night['DET2.SEQ1.DIT']==m[2])*\
            ( (night['DPR.CATG']=='SCIENCE')*(night['dist']<dist_target) + 
              (night['DPR.CATG']!='SCIENCE')*(night['dist']<dist_calib) ) 
        w *= np.array([typ.split(',')[0] in ['STD', 'SKY', 'OBJECT'] for typ in night['DPR.TYPE']])
        if not sum(w):
            print('no data?')
            continue
        if verbose:
            print('\non sky data for', m)
            night[w]['TPL.START', 'OBS.TARG.NAME', 'DPR.CATG', 'RA', 'DEC', 'dist', 'ProgId',
                    'ISS.CONF.STATION1', 'ISS.CONF.STATION2', 'ISS.CONF.STATION3', 'ISS.CONF.STATION4'].pprint(max_width=100, max_lines=100,show_name=False)
        dpid.extend(night[w]['DP.ID'])

        if withP2vm:
            p2vm = []
            i = 0
            while len(p2vm)==0 and i<len(dt):
                p2vm = getP2vm(starttime, spec=m[0], pola=m[1], delta_day=dt[i])
                i += 1
            if verbose:
                print('\nP2VM')
                p2vm['TPL.START', 'DPR.CATG', 'DPR.TYPE', 'DET2.SEQ1.DIT'].pprint(max_width=100, max_lines=100,show_name=False)
            if len(p2vm)==0:
                print('WARNING: no P2VM found +/- %d days from observations'%calibValidity)
            else:
                dpid.extend(p2vm['DP.ID'])
        
        dark = []
        i = 0
        while len(dark)==0 and i<len(dt):
            dark = getDark(starttime, spec=m[0], pola=m[1], dit=m[2], delta_day=dt[i])
            i += 1  
        if verbose:
            print('\nDARK')
            dark['TPL.START', 'DPR.CATG', 'DPR.TYPE', 'DET2.SEQ1.DIT'].pprint(max_width=100, max_lines=100,show_name=False)
        if len(dark)==0:
            print('WARNING: no DARK found +/- %d days from observations'%calibValidity)
        else:
            dpid.extend(dark['DP.ID'])
    return dpid

def getStartDate(target, stime=None, etime=None):
    # -- get the date at which the object was observed:
    col_filter = {'target':target}
    if not stime is None:
        col_filter['stime'] = stime
    if not etime is None:
        col_filter['etime'] = etime
    else:
        # -- force query to now
        t = time.gmtime()
        col_filter['etime'] = '%4d-%02d-%02d'%(t.tm_year, t.tm_mon, t.tm_mday)
        
    table = eso.query_instrument('gravity', column_filters=col_filter, dp_cat='SCIENCE')
    # -- List the starting dates of the nights
    # -- can be misleading because UT date changes during the night in Paranal 
    mjd = [Time(d).mjd for d in table['TPL.START']]
    times = sorted(list(set([Time(int(m+0.2)-0.2, format='mjd').isot for m in mjd])))
    return times

def pidAllCalib(date, spec, pola, dit, delta_day=0, verbose=False):
    """
    get PIDs of files from P2VMs and DARKS for a given setup, on a given date:
    
    date: UT date of the day the night started (usually -1d compared to UT dates in actual file)
    spec: spectral resolution, eg 'LOW', 'MEDIUM', or 'HIGH'
    pola: 'COMBINED' or 'SPLIT'
    dit: SC observation's DIT (for the darks), in seconds
    delta_day: -1 to get the P2VM on previous day, +1 for the following day etc [default is 0] 
    
    returns: filename where PIDs were written. Use it for:
    http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html
    """
    p2vms = getP2vm(date, spec=spec, pola=pola, delta_day=delta_day)
    darks = getDark(date, spec='MEDIUM', pola='COMBINED', dit=dit, delta_day=delta_day)
    if verbose:
        print('## P2VM', '#'*20)
        p2vms['DP.ID', 'TPL.START', 'DPR.CATG', 'DPR.TYPE', 'DET2.SEQ1.DIT'].pprint(max_width=100, max_lines=100,show_name=False)
        print('## Darks', '#'*20)
        darks['DP.ID', 'TPL.START', 'DPR.CATG', 'DPR.TYPE', 'DET2.SEQ1.DIT'].pprint(max_width=100, max_lines=100,show_name=False)
    filename = '%s_%s_%s_DIT%d_dd%d.txt'%(date, spec, pola, int(dit), delta_day)
    with open(filename, 'w') as f:
        for l in p2vms:
            f.write(l['DP.ID']+'\n')
        for l in darks:
            f.write(l['DP.ID']+'\n')
    return filename
#date, spec, pola, dit, dd = '2022-01-22', 'MEDIUM', 'COMBINED', 3, 0
#pidAllCalib(date, spec, pola, dit, dd, verbose=False)
print('done on:', time.asctime())