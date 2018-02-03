import struct
import os
import gzip
import zlib

class DictZip:
    def __init__(self, name):
        self.name = name
        self.deflate = zlib.decompressobj(-15)
        self.fd = open(name, 'rb')
        t = self._read_header(self.fd)
        self.chlen   = t[0]
        self.sizes   = t[1]
        self.offsets = t[2]
        self.chcnt = len(self.sizes)

    def _read_header(self, f):
        f.seek(0)
        # check header parameters
        header = f.read(10)
        if header[:2] != b'\x1f\x8b':
            raise ValueError('gzip signature expected')
        if (header[2]) != 8:
            raise ValueError('only DEFLATE archives supported')
        flags = (header[3])
        if not flags&(1<<2):
            raise ValueError('extra dictzip field expected')
        # read dictzip data
        XLEN, SI1, SI2, LEN = struct.unpack('<H2cH', f.read(6))
        if SI1+SI2 != b'RA':
            raise ValueError("'RA' signature expected")
        data = f.read(LEN)
        VER, CHLEN, CHCNT = struct.unpack('<3H', data[:6])
        sizes = struct.unpack('<'+str(CHCNT)+'H', data[6:])
        # skip filename if present
        if flags&(1<<3):
            while self.fd.read(1) != b'\x00':
                pass
        # transform sizes into start offsets of chunks
        ofs = [self.fd.tell()]
        for s in sizes[:-1]:
            ofs.append(ofs[-1]+s)
        return CHLEN, sizes, ofs

    def seek(self, offset):
        'only to provide file-like interface'
        self.offset = offset

    def read(self, size):
        '''
        determines which chunk to read and decompress
        it's possible that data overrun to the following chunk
        so this must be handled too
        '''
        chunk = self.offset//self.chlen
        self.fd.seek(self.offsets[chunk])
        compr = self.fd.read(self.sizes[chunk])
        data = self.deflate.decompress(compr)
        # offset in the chunk
        chofs = self.offset % self.chlen
        if chofs+size > self.chlen:
            # data continue in the next chunk
            out = data[chofs:]
            self.seek(self.offset+len(out))
            out += self.read(size-len(out))
        else:
            # all in the current chunk
            out = data[chofs:chofs+size]
        return out

    def close(self):
        self.fd.close()


class StarDict:
    def __init__(self, ifopath, load=True):
        self.fname = ifopath[:-4]
        self._check_files()
        if load:
            self.load()
        else:
            self.idx = []

    def _check_files(self):
        'loads .ifo information'
        'and checks all needed dictionary files are present'
        name = self.fname
        self.ifo = {}
        for l in open(name+'.ifo').readlines()[1:]:
            pair = l.split('=')
            self.ifo[pair[0]] = pair[1][:-1]

        if (self.ifo['version'] not in ('2.4.2', '3.0.0') or
            self.ifo['sametypesequence'] != 'g'):
            raise ValueError('unsupported StarDict')

        if (not os.path.exists(name+'.idx')):
            raise ValueError('missing .idx file')

        if (not os.path.exists(name+'.dict') and
            not os.path.exists(name+'.dict.dz')):
            raise ValueError('missing .dict file')

    def load(self):
        '''
        from .idx builds a list of (word, (dict_index, length)) tuples
        and opens .dict[.dz] file for reading
        '''
        fname = self.fname+'.idx'
        f = open(fname, 'rb')
        flen = os.path.getsize(fname)
        data = f.read(flen)
        f.close()
        self.idx = []
        a = 0
        b = data.find(b'\0', a)
        while b > 0:
            self.idx.append((data[a:b].decode('utf8'),
                             struct.unpack('>LL', data[b+1:b+9])
                             ))
            a = b+9
            b = data.find(b'\0', a)
        assert int(self.ifo['wordcount']) == len(self.idx)
        # compression of .dict is optional
        try:
            self.dictf = open(self.fname+'.dict', 'rb')
        except OSError:
            self.dictf = DictZip(self.fname+'.dict.dz') 

    def unload(self):
        'releases idx word list and opened .dict file'
        self.idx = []
        self.dictf.close()

    def __len__(self):
        return len(self.idx)

    def __getitem__(self, key):
        ''' 
        int and slice return coresponding words
        string key is used for reverse lookup
        '''
        if type(key) is int:
            return self.idx[key][0]
        if type(key) is slice:
            return [w[0] for w in self.idx[key]]
        if type(key) is str:
            index = self.search(key)
            if index < 0:
                raise IndexError
            return index

    def search(self, word, prefix=False):
        '''
        binary search for words in idx list
        when prefix=True it searches for the lowest record
        with 'word' as its prefix
        '''
        if word == '':
            return -1
        a, b = 0, len(self.idx)-1
        if (b<0):
             return -1
        word = word.lower()
        while a <= b:                
            i = a+(b-a)//2
            if prefix:
            # searches words that include 'word' in their prefix
                if self.idx[i][0].lower().startswith(word):
                    if i and self.idx[i-1][0].lower().startswith(word):
                        b = i-1
                        continue
                    else:
                        return i
            else:
            # searches for entire match
                if self.idx[i][0].lower() == word:
                    return i
            if a == b:
                # no match
                return -1
            elif word > self.idx[i][0].lower():
                # move upward
                a = i+1
            else:
                # move downward
                b = i-1
        return -1
    
    def dict_link(self, index):
        'returns (dict_index, len) tuple of a word on a given index'
        return self.idx[index][1]

    def dict_data(self, index):
        'returns translation for a word on the given index'
        self.dictf.seek(self.idx[index][1][0])
        return self.dictf.read(self.idx[index][1][1])

    def __str__(self):
        return str(self.ifo)


def look_for_dicts(path):
    '''
    explores all subdirectories of path searching for filenames
    that have all three .ifo, .idx and .dict[.dz] suffixes
    '''
    names = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if not f.endswith('.ifo'):
                continue
            name = f[:-4]
            if (name+'.idx' in files and (name+'.dict.dz' in files
                                          or name+'.dict' in files)):
                names.append(root+'/'+name+'.ifo')
    return names
        

if __name__ == '__main__':

    dicts = look_for_dicts('C:\\Users\\blang\\OneDrive\\PythonProjects\\WatchDicHistory\\pyStarDictViewer\\dic')
    for d in dicts:
        print(d)
    dict = StarDict(dicts[0], False)
    i = dict.search('a',True)
    print("this is 'a' in dictionary:" +  str(i) )
    dz = DictZip(dicts[0][:-4]+'.dict.dz')
    dz.seek(dz.chlen-10)
    print(dz.read(20))


'''
For Python 3.5+ use:

import importlib.util
spec = importlib.util.spec_from_file_location("stardict", "C:\\Users\\blang\\OneDrive\\PythonProjects\\WatchDicHistory\\pyStarDictViewer\\api_stardict.py")
foo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foo)
dicts = foo.look_for_dicts("C:\\Users\\blang\\OneDrive\\PythonProjects\\WatchDicHistory\\pyStarDictViewer\\dic")


foo.MyClass()
'''