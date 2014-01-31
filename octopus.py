#!/usr/bin/python

# Octopus! sounds goood :-)

# Notes:
# * You will need to normalize the tracks after Octopus! is done.
#   I recomend http://mp3gain.sourceforge.net/ Linux and OS X
#   versions are available. "Radio Gain Mode" and Gain Value 89 db recommended.
# * Only reencoding mp3, wav, m4a, aac and flac

import os
import sys
import time
import random
import datetime
import multiprocessing
from subprocess import Popen, PIPE
from progressbar import ProgressBar

__author__ = "Timothy Makobu"

# config -- set paths to required binaries  #
config = {
    'lame':r'/opt/local/bin/lame',
    'faad':r'/opt/local/bin/faad',
    'flac':r'/opt/local/bin/flac',
    'lameopts':['-m', 's', '-q', '0', '--vbr-new', '-V', '0', '-b', '128', '-B', '192', '--silent'],
    'max_proc':10,
}

for path in [config.get('paths', x) for x in config.options('paths')]:
    if not os.path.isfile(path):
        print '%s is not a file; exiting ...' % path
        sys.exit()
# *** #

# Transcode factory
def reencode_mp3(tune):
    try:
        trash_can.write(''.join(Popen([lame, tune]+lameopts, stdout=PIPE, stderr=PIPE).communicate()))
        os.rename(os.path.splitext(tune)[0]+'.mp3.mp3', tune)
    except OSError,e:
        octo_error_log(path, str(e))
        pass

def reencode_wav_to_mp3(tune):    
    try:
        trash_can.write(''.join(Popen([lame, tune]+lameopts, stdout=PIPE, stderr=PIPE).communicate()))
        os.remove(tune)
        os.rename(tune+'.mp3', os.path.splitext(tune)[0] + '.mp3')
    except OSError, e:
        octo_error_log(path, str(e))
        pass

def reencode_itunes_to_mp3(tune):
    try:
        trash_can.write(''.join(Popen([faad, '-q', '-o', os.path.splitext(tune)[0] + '.wav', tune], stdout=PIPE, stderr=PIPE).communicate()))
        os.remove(tune)
        trash_can.write(''.join(Popen([lame, os.path.splitext(tune)[0] + '.wav']+lameopts, stdout=PIPE, stderr=PIPE).communicate()))
        os.remove(os.path.splitext(tune)[0] + '.wav')
        os.rename(os.path.splitext(tune)[0] + '.wav.mp3', os.path.splitext(tune)[0] + '.mp3')
    except OSError,e:
        octo_error_log(path, str(e))
        pass

def reencode_flac_to_mp3(tune):
    try:
        trash_can.write(''.join(Popen([flac, '-ds', tune], stdout=PIPE, stderr=PIPE).communicate()))
        os.remove(tune)
        trash_can.write(''.join(Popen([lame, os.path.splitext(tune)[0] + '.wav']+lameopts, stdout=PIPE, stderr=PIPE).communicate()))
        os.remove(os.path.splitext(tune)[0] + '.wav')
        os.rename(os.path.splitext(tune)[0] + '.wav.mp3', os.path.splitext(tune)[0] + '.mp3')
    except OSError,e:
        octo_error_log(path, str(e))
        pass

# Utility functions
def get_tunes(path):
    for fileb in os.walk(path):
        for tune in fileb[2]:
            if os.path.splitext(os.path.join(fileb[0], tune))[1] in ('.mp3','.wav','.acc','.m4a','.flac'):
                yield os.path.join(fileb[0], tune)

def normalize_extension_case(path):
    for fileb in os.walk(path):
        for tune in fileb[2]:
            if os.path.splitext(os.path.join(fileb[0], tune))[1] in ('.MP3','.WAV','.ACC','.M4A','.FLAC'):
                oldSong = os.path.join(fileb[0], tune)
                newSong = os.path.splitext(os.path.join(fileb[0], tune))[0]+os.path.splitext(os.path.join(fileb[0], tune))[1].lower()
                os.rename(oldSong, newSong)
    
def get_dir_size(path):
    dirSize = 0
    for (fpath, dirs, files) in os.walk(path):
        for file in files:
            filename = os.path.join(fpath, file)
            dirSize += os.path.getsize(filename)
    return dirSize

def octo_log(path, message, p=True):
    if p:
        print message.replace('<br>', '\n')
    fh = file(os.path.join(path, 'OCTOPUS-LOG.html'), 'a')
    fh.write(message+'<br>')
    fh.close()

def octo_error_log(path, message):
    fh = file(os.path.join(path, 'error_log.html'), 'a')
    fh.write(message+'<br>')
    fh.close()

def get_tune_count(path):
    tune_count = 0
    for fileb in os.walk(path):
        for tune in fileb[2]:
            if os.path.splitext(os.path.join(fileb[0], tune))[1] in ('.mp3','.wav','.acc','.m4a','.flac'):
                tune_count += 1
    return tune_count


# Managers
def dispatcher(tune):
    ext = os.path.splitext(tune)[1]
    if ext == '.mp3':
        reencode_mp3(tune)
    elif ext == '.wav':
        reencode_wav_to_mp3(tune)
    elif ext in ('.acc','.m4a'):
        reencode_itunes_to_mp3(tune)
    elif ext == '.flac':
        reencode_flac_to_mp3(tune)

def main():
    if not os.path.isdir(path):
        raw_input("%s is not a valid folder. Press ENTER to exit ..." % path)
        sys.exit()
    
    curr_tune = 1
    tune_count = get_tune_count(path)

    if not tune_count:
        raw_input("Found %d tacks to re-encode. Press ENTER to exit ..." % tune_count)
        sys.exit()
    if raw_input('\nOk; ready to reencode %d tracks.\nHave you backed up the\n[%s]\nfolder??? [y/N]: ' % (tune_count, path)).lower() != 'y':
        sys.exit()
    
    for log_file in ('OCTOPUS-LOG.html', 'error_log.html'):
        if os.path.isfile(os.path.join(path, log_file)):
            os.remove(os.path.join(path, log_file))
    
    octo_log(path, '<head><title>OCTOPUS-LOG</title></head>', p=False)
    octo_log(path, '<b>Octopus!</b> Sounds goood :)<br>', p=False)
    proc_count = multiprocessing.cpu_count() * 2
    if proc_count > config['max_proc']: proc_count = config['max_proc']
    start_time = time.time()
    octo_log(path, 'Spawning [[ %d ]] workers ...' % proc_count)
    octo_log(path, 'Start time: '+ time.strftime('%a, %b %d, %Y at %I:%M:%S %p', time.localtime(start_time)))
    octo_log(path, 'Setting track(s) extension(s) to lower case ...')
    normalize_extension_case(path)
    octo_log(path, 'Size Before Re-encode: %d MiB' % (get_dir_size(path)/1048576))
    octo_log(path, 'Re-encoding %d track(s) ...<br>' % tune_count)
    
    pool = multiprocessing.Pool(proc_count)
    progress_bar = ProgressBar(maxval=tune_count)
    for i,exhaust in zip(progress_bar(xrange(tune_count)), pool.imap(dispatcher, get_tunes(path))):
        time.sleep(random.randint(7,14) / 10)
        del(exhaust)

    octo_log(path, "<br>Success!<br>")
    end_time = time.time()
    octo_log(path, 'End time: '+time.strftime('%a, %b %d, %Y at %I:%M:%S %p', time.localtime(end_time)))
    octo_log(path, 're-encoded %d track(s) in %7.2f seconds, [%5.2f minutes]' % (tune_count, end_time - start_time, (end_time - start_time)/60))
    octo_log(path, 'Size After Re-encode: %d MiB' % (get_dir_size(path)/1048576))
    print "\nRock on! :-)"
    octo_log(path, '<p><a href="http://tims-octopus.googlecode.com/">http://tims-octopus.googlecode.com</a>\
    </p><p>(C)%s %s</p>' % (datetime.date.today().year,__author__), p=False)


if __name__ == '__main__':
    #if sys.platform not in ['darwin','linux']:
    #    if raw_input('This script runs best on OS X and Linux. You sure you want to continue? [y/N]').lower() != 'y':
    #        sys.exit()

    try:
        #locals().update(config)
        trash_can = open(os.devnull, 'w')
        path = raw_input('Type path to music folder (Example: /home/me/Music): ').strip()
        sys.exit(main())
    except KeyboardInterrupt:
        print;sys.exit()