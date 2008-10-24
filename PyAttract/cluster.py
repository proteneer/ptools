#!/usr/bin/env python

##
## script to cluster solutions generated by Attract
## 
## usage : cluster2.py arg1 arg2 [options]
##
## arg1 : output file generated by attract_ff2.py script
## arg2 : ligand file use during the docking procedure
## options :
##
## if you want to modify the cutoff value when comparing Rmsd or energy, 
## specify the -r or -e option (default value for both = 1.0)
## if you want to increase the number of best solution (according to the energy) that are clustered
## specify the -s (or --structure_cutoff) option. (default=2000)
## if you want to increase the number of cluster that are compared to the current structure 
## during the clustering process, specify the -c (or --cluster_cutoff) option (default=50)
##
## for example, to increase the scut and increase the Rmsd cutoff value,
## the following command should be used:
## > cluster2.py arg1 agr2 -scut 5000 -r 1.5
##

import sys
from ptools import *
from optparse import OptionParser
parser = OptionParser()
parser.usage = 'cluster.py <out_file> <lig_file> [options]'
parser.add_option("-e", "--energy_cutoff", action="store", type="float", dest="energy_cutoff", help="Energy cutoff value (default=1000.0)")
parser.add_option("-r", "--rmsd_cutoff", action="store", type="float", dest="rmsd_cutoff", help="Rmsd cutoff value (default=1.0)")
parser.add_option("-s", "--structure_cutoff", action="store", type="int", dest="structure_cutoff", help="number of structures to cluster, an increase of this value will increase significantly the time processing (default = 2000)")
parser.add_option("-c", "--cluster_cutoff", action="store", type="int", dest="cluster_cutoff", help="number of cluster that are compared during the clustering process, an increase of this value will increase significantly the time processing  (default=50)")
(options, args) = parser.parse_args()


########################
# from Extract.py

class StructureI:
    def __cmp__(self, other):
            if self.trans < other.trans:
                return -1
            if self.trans > other.trans:
                return 1
            return cmp(self.rot, other.rot)
    pass




def rigidXMat44(rigid, mat):
    assert(isinstance(rigid,Rigidbody))
    out=Rigidbody(rigid)
    for i in range(rigid.Size()):
        coords=rigid.GetCoords(i)
        coords2=Coord3D()
        coords2.x = mat[0][0]*coords.x + mat[0][1]*coords.y + mat[0][2]*coords.z + mat[0][3]
        coords2.y = mat[1][0]*coords.x + mat[1][1]*coords.y + mat[1][2]*coords.z + mat[1][3]
        coords2.z = mat[2][0]*coords.x + mat[2][1]*coords.y + mat[2][2]*coords.z + mat[2][3]
        out.SetCoords(i, coords2)
    return out



def readStructures(file):


    out_attach = open(file,'r')
    #determine output format version:
    firstline = out_attach.readline()
    firstline = firstline.split()
    if (len(firstline) == 0):
        outversion = 1
    else:
        outversion = int(firstline[0])

    #now read all lines until it finds a line like: "==        1      1   -14.0032942 94.6604593764"
    # (version 1)

    if outversion == 1 :
        structures = {}
        lststructures = []
        #structures = []
        #dicstruct = {}
        begin=False
        lines = out_attach.readlines()
        for l in lines:
            lspl = l.split()
            if len(lspl) >0 and lspl[0] == "==":
                begin = True
                struct = StructureI()
                struct.trans = int(lspl[1])
                struct.rot = int(lspl[2])
                struct.ener = float(lspl[3])
                struct.rmsd = lspl[4]
                matrix=[]
            if (begin):
                lspl = l.split()
                if lspl[0]=="MAT":
                    matrix.append( [float(lspl[i]) for i in range(1,5) ]  )
                else:
                    if lspl[2] == "END":
                        begin = False
                        struct.matrix = matrix
                        structures.setdefault(struct.trans,{})[struct.rot]=struct
                        lststructures.append(struct)
                        #structures.append(struct)


    return structures,lststructures


######################


outputfile = sys.argv[1]
ligandfile = sys.argv[2]


_,structures = readStructures(outputfile)

#print "sorting energies"
structures.sort(key=lambda i: i.ener)
#print "sorting done"

cluster = []
lig = Rigidbody(ligandfile)

class Struct:
    structure = None
    count = 0


limit_rmsd = 1.0 
limit_ener = 1000.0 
structure_cutoff=2000
cluster_cutoff=50
cluster_cutoff_=cluster_cutoff+1

if (options.energy_cutoff):
	limit_ener=options.energy_cutoff
if (options.rmsd_cutoff):
	limit_rmsd=options.rmsd_cutoff
if (options.structure_cutoff):
	structure_cutoff=options.structure_cutoff
if (options.cluster_cutoff):
	cluster_cutoff=options.cluster_cutoff
	cluster_cutoff_=options.cluster_cutoff+1



for s in structures[:structure_cutoff]:
    if s.ener>0:
        break
    new=True
    sc = rigidXMat44(lig,s.matrix)

    for c in reversed(cluster[-cluster_cutoff:]):
	if ( ( c.ext.ener-s.ener < limit_ener ) and ( Rmsd(sc,c.structure) < limit_rmsd ) ):
	#if Rmsd(sc,c.structure)< limit_rmsd:
            c.count += 1
            new=False
            #print "stuct added to a cluster"
            break
    if new==True:
        c = Struct()
        c.structure = sc
        c.ext = s
        c.count = 1
        cluster.append(c)
        if len(cluster) > cluster_cutoff:
           del cluster[-cluster_cutoff_].structure
        #print "new cluster"


#cluster.sort(key=lambda i: i.ext.ener)
#print "number of clusters:", len(cluster)
#print "first clusters (by energy) sizes:",
#for i in xrange(30):
    #print cluster[i].count,

#cluster.sort(key=lambda i: i.count, reverse=True)
#print "first clusters (by size):",
#for i in xrange(30):
    #print cluster[i].count,

cluster.sort(key=lambda i: i.ext.ener)
print "%-4s %6s %6s %13s %13s %6s %8s"  %(" ","Trans", "Rot", "Ener", "RmsdCA_ref","Rank", "Weight")
for i in range(len(cluster)):
	print "%-4s %6s %6s %13.7f %13.7f %6i %8s" %("==", str(cluster[i].ext.trans), str(cluster[i].ext.rot), float(cluster[i].ext.ener), float(cluster[i].ext.rmsd), i+1, str(cluster[i].count))
