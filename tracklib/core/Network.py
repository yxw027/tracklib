# -------------------------- Network ------------------------------------------
# Class to manage Network
# -----------------------------------------------------------------------------
import random
import matplotlib.pyplot as plt

from tracklib.core.Track import Track
from tracklib.core.GPSTime import GPSTime
from tracklib.core.Obs import Obs
from tracklib.core.Operator import Operator

import tracklib.algo.Summarize as Sum

# =============================================================================
#
#
AF_LINK = "#link"
AF_WEIGHT = "#weight"
# =============================================================================
#
#
class Node:
    
    def __init__(self, id, coord):
        
        self.id = id
        self.coord = coord
        
        self.entrants = []
        self.sortants = []
        
        # Pour le ppc:
        self.initializeForSP()
        
    def __hash__(self):
        return hash(self.id)
        
    def plot(self, sym='r+'):
        plt.plot(self.coord.getX(), self.coord.getY(), sym)
               
    def initializeForSP(self):
        self.__noeudPrecedent = None
        self.__distance = -1
        self.__arcPrecedent = None
        
    def getDistance(self):
        return self.__distance
        
    def getArcsEntrants(self):
        return self.entrants
    
    def getArcsSortants(self):
        return self.sortants
    
    def addArcSortant(self, edge):
        self.sortants.append(edge)

    def addArcEntrant(self, edge):
        self.entrants.append(edge)

    def plusCourtChemin(self, arrivee, lengthmax = 0):
        '''
        Plus court chemin de self vers arrivée, en tenant compte du sens de circulation. 
        Le pcc s'appuie sur l'attribut 'poids' des arcs, qui doit être rempli auparavant.
        
        @param lengthmax Pour optimiser: on arrête de chercher et on renvoie une trace vide
             s'il n'y a pas de pcc de taille inférieure à maxLongueur (inactif
             si maxLongueur = 0).
        '''
        PPC = []
        
        if self == arrivee:
            trace = Track()
            trace.addObs(Obs(self.coord, GPSTime()))
            # PPC.add(self)
            # return PPC
            return trace
        
        self.__distance = 0
        
        (arcsVoisins, noeudsVoisins, distancesVoisins) = self.__chercheArcsNoeudsVoisins()
    
        noeudsTraites = []
        noeudsATraiter = []
        
        for i in range(len(noeudsVoisins)):
            noeudVoisin = noeudsVoisins[i]
            arcVoisin = arcsVoisins[i]
            dist = float(distancesVoisins[i])
            noeudVoisin.__distance = dist
            noeudVoisin.__arcPrecedent = arcVoisin
            noeudVoisin.__noeudPrecedent = self
      
        noeudsATraiter += noeudsVoisins
        
        # Phase "avant"
        while len(noeudsATraiter) > 0:
            # on choisit le noeud à marquer comme traité parmi les voisins
            plusProche = noeudsATraiter[0]
            for i in range(1, len(noeudsATraiter)):
                if noeudsATraiter[i].__distance < plusProche.__distance:
                    plusProche = noeudsATraiter[i]

            noeudsTraites.append(plusProche)
            noeudsATraiter.remove(plusProche)
            
            # Il s'agit du noeud d'arrivée
            if plusProche == arrivee:
                # Arrivé !!!
                break
            
            if lengthmax > 0:
                if plusProche.__distance > lengthmax:
                    # Trop long, on s'arrête et on renvoie une trace vide
                    trace = Track()
                    return trace
                  
            (arcsVoisins, noeudsVoisins, distancesVoisins) = plusProche.__chercheArcsNoeudsVoisins()
            
            for i in range(len(noeudsVoisins)):
                noeudVoisin = noeudsVoisins[i]
                arcVoisin = arcsVoisins[i]
                dist = float(distancesVoisins[i])
                
                if noeudVoisin in noeudsTraites:
                    # Noeud est déjà traité
                    continue
                
                if noeudVoisin in noeudsATraiter:
                    # Noeud déjà atteint, on voit si on a trouvé 
                    #       un chemin plus court pour y accèder
                    if noeudVoisin.__distance > (plusProche.__distance + dist):
                        noeudVoisin.__distance = plusProche.__distance + dist
                        noeudVoisin.__arcPrecedent = arcVoisin
                        noeudVoisin.__noeudPrecedent = plusProche
            
                    continue
          
                # Nouveau noeud atteint, on l'initialise
                noeudVoisin.__distance = plusProche.__distance + dist
                noeudVoisin.__arcPrecedent = arcVoisin
                noeudVoisin.__noeudPrecedent = plusProche
                noeudsATraiter.append(noeudVoisin)
        
        
        # Phase "arriere"
        if arrivee not in noeudsTraites:
            # Couldn't reach it
            # sys.exit("Error: Couldn't reach it")
            return None
        
        if arrivee not in PPC:
            PPC.append(arrivee)
            
        arcsFinaux = []
        noeudsFinaux = []
        
        suivant = arrivee

        while (True):
            arcsFinaux.insert(0, suivant.__arcPrecedent)
            if suivant.__arcPrecedent not in PPC:
                PPC.append(suivant.__arcPrecedent)
            suivant = suivant.__noeudPrecedent
            if suivant == self:
                break
        
            noeudsFinaux.insert(0, suivant)
            if suivant not in PPC:
                PPC.append(suivant)
                
        noeudsFinaux.insert(0, self)
        if self not in PPC:
            PPC.append(self)
        noeudsFinaux.insert(0, arrivee)

        # On construit le PCC en Track
        trace = Track()
        
        LINKS = []
        DIST_TAB = []
        
        for i in range(len(PPC)-2, -1, -2):
            elt = PPC[i]
            node = PPC[i+1]
            portion = elt.track.getObsList()
            
            # Si la géometrie est inversée
            if elt.track.getLastObs().position.distance2DTo(node.coord) == 0:
                 portion = portion[::-1]
                 
        #     #if elt.track.getFirstObs().position.distance2DTo(node.coord) == 0:
        #     #     portion = portion[1::-1]
            for o in portion:
                trace.addObs(o)
                DIST_TAB.append(node.getDistance())
                LINKS.append(elt.id)
                
        # Le dernier point
        node0 = PPC[0]
        DIST_TAB[len(DIST_TAB)-1] = node0.getDistance()
        
        trace.createAnalyticalFeature(AF_LINK, LINKS)
        trace.createAnalyticalFeature(AF_WEIGHT, DIST_TAB)
        
        return trace
            
    
    def __chercheArcsNoeudsVoisins(self):
        '''
            Tient compte du sens de la circulation
        '''
        noeudsVoisins = []
        distancesVoisins = []
        arcsVoisins = []
        
        arcsEntrants = self.getArcsEntrants()
        arcsSortants = self.getArcsSortants()
        
        # transformation du sens géométrique au sens de circulation
        for arc in arcsEntrants:
            if arc.getOrientation() == -1 or arc.getOrientation() == 0:
                if arc.getNoeudIni() != None:
                    arcsVoisins.append(arc)
                    noeudsVoisins.append(arc.getNoeudIni())
                    distancesVoisins.append(arc.getPoids())
        for arc in arcsSortants:
            if arc.getOrientation() == 1 or arc.getOrientation() == 0:
                if arc.getNoeudFin() != None:
                    arcsVoisins.append(arc)
                    noeudsVoisins.append(arc.getNoeudFin())
                    distancesVoisins.append(arc.getPoids())
        
        return (arcsVoisins, noeudsVoisins, distancesVoisins)
    
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        if self.id == other.id:
            return True
        return False
        
    def __str__(self):
        return "Node object: " + str(self.id)
        

# =============================================================================
#
#
class Edge:
    
    '''
    Sens de l'attribut du troncon et pas celui de la géométrie
    '''
    DOUBLE_SENS  = 0
    SENS_DIRECT  = 1
    SENS_INVERSE = -1
    
    def __init__(self, id, track):
        
        self.id = id
        self.track = track
        
        self.noeudIni = None
        self.noeudFin = None
        self.orientation = 0
        self.poids = 0
        
    def __hash__(self):
        return hash(self.id)
        
    def getNoeudIni(self):
        return self.noeudIni
    
    def setNoeudIni(self, noeud):
        
        if self.noeudIni != None:
            self.noeudIni.getArcsSortants().remove(self)
    
        if noeud != None:
            self.noeudIni = noeud
      
        if self not in noeud.getArcsSortants():
            noeud.addArcSortant(self)
        else:
            self.noeudIni = None
    
    def getNoeudFin(self):
        return self.noeudFin
    
    def setNoeudFin(self, noeud):
        #self.noeudFin = noeudFin
        
        if self.noeudFin != None:
            self.getNoeudFin().getArcsEntrants().remove(self)
    
        if noeud != None:
            self.noeudFin = noeud
      
        if self not in noeud.getArcsEntrants():
            noeud.addArcEntrant(self)
        else:
            self.noeudFin = None
    
      
        
    def setOrientation(self, orientation):
        self.orientation = orientation
    def getOrientation(self):
        return self.orientation
        
    def setPoids(self, poids):
        self.poids = poids
    def getPoids(self):
        return self.poids
        
    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        if self.id == other.id:
            return True
        return False

    def __str__(self):
        return 'edge #' + str(self.id)
    
    def getX(self, i=None):
        return self.track.getX(i)

    def getY(self, i=None):
        return self.track.getY(i)

# =============================================================================
#
#
class Network:

    def __init__(self):
        '''
        '''
        self.EDGES = dict()
        self.NODES = dict()
        
        self.__idx_nodes = []
        self.__idx_edges = []
        
        self.__cut = 0
        
        
    def __iter__(self):
        yield from [l[1] for l in list(self.EDGES.items())]
        
    def size(self):
        return len(self.EDGES)
    
    # ------------------------------------------------------------
    # [[n]] Get and set an edge from n
    # ------------------------------------------------------------    
    def __getitem__(self, n):
        return self.EDGES[self.__idx_edges[n]]
    def __setitem__(self, n, edge):
        self.EDGES[self.__idx_edges[id]] = edge  
        
    def getIndexNodes(self):
        return self.__idx_nodes
        
    def getNumberOfNodes(self):
        return len(self.NODES)
    def getNumberOfEdges(self):
        return len(self.EDGES)
        
    def getNodeId(self, n):
        return self.__idx_nodes[n]
    def getEdgeId(self, n):
        return self.__idx_edges[n]
    def getNodesId(self):
        return [l[0] for l in list(self.NODES.items())]
    def getEdgesId(self):
        return [l[0] for l in list(self.EDGES.items())]
        
    def getRandomNode(self):
        return self.getNode(self.getNodesId()[random.randint(0, self.getNumberOfNodes())])
        
    def addNode(self, node):
        self.NODES[node.id] = node
        self.__idx_nodes.append(node.id)
    def addEdge(self, edge):
        self.EDGES[edge.id] = edge  
        self.__idx_edges.append(edge.id)

    def hasNode(self, id):
        return id in self.NODES  
    def hasEdge(self, id):
        return id in self.EDGES

    def getNode(self, id):
        return self.NODES[id]
    def getEdge(self, id):
        return self.EDGES[id]    
    
    def select(self, node, distance):
        '''
        Selection des autres noeuds dans le cercle dont node.coord est le centre, 
        de rayon distance

        Parameters
        ----------
        node : Node
            le centre du cercle de recherche.
        tolerance : double
            le rayon du cercle de recherche.

        Returns
        -------
        NODES : tableau de NODES
            liste des noeuds dans le cercle

        '''
        NODES = []
        
        for key in self.NODES:
            n = self.NODES[key]
            if n.coord.distance2DTo(node.coord) <= distance:
                NODES.append(n)
        
        return NODES
    
    
    def __initializeForSP(self):
        for i in range(self.getNumberOfNodes()):
            node = self.getNode(self.getNodeId(i))
            node.initializeForSP()
            
    
    def shortest_path(self, node1, node2, cut = 0):
        self.__cut = cut
        self.__initializeForSP()
        return node1.plusCourtChemin(node2, cut)
    
    
    def shortest_path_distance(self, node1, node2, cut = 0):
        self.__cut = cut
        self.__initializeForSP()
        trace = node1.plusCourtChemin(node2, cut)
        if trace != None and trace.hasAnalyticalFeature(AF_WEIGHT):
            DISTS = trace.getAnalyticalFeature(AF_WEIGHT)
            return DISTS[len(DISTS) - 1]
        else:
            return None
    
    
    def shortest_path_distances(self, node1, cut=0):
        '''
        
        Il faut avoir lancé un shortest_path avant !
        
        retourne un dict  (key = node1 - node, val = distance)
        
        Une fonction plus efficace pour le calcul global, qui donne les distances 
        des plus courts chemins entre node1 et tous les nœuds du réseau. 
        Lorsque cut est renseigné, on arrête le calcul dès qu’on dépasse 
        la distance cut. Par exemple : shortest_path_distances(n, 300) va 
        retourner les plus courtes distances de n à tous les autres nœuds 
        du réseau situés à moins de 300 unités
        
        cette fonction (dite de Dijkstra omnidirectionnel) est en réalité 
        la sortie de base de Dijkstra. Il ne faut pas calculer n fois un 
        Dijkstra unidirectionnel.
        '''
        
        if cut > 0:
            self.__cut = cut
        # sinon cut peut avoir été utilisé dans le calcul
        
#        for edge in self.EDGES:
#            X = edge.track.getX()
#            Y = edge.track.getY()
#            if edge.orientation == Edge.DOUBLE_SENS:
#                plt.plot(X, Y, '-', color="blue", linewidth = 0.5)
#            else:
#                plt.plot(X, Y, '-', color="gray", linewidth = 0.5)
#        
#        for node in self.NODES:
#            distance = node.getDistance()
#            if distance < 0:
#                plt.plot(node.coord.getX(), node.coord.getY(), 'bo')
#                
#        if node1 != None:
#            plt.plot(node1.coord.getX(), node1.coord.getY(), 'rx', markersize=5)
#                
#        plt.show()
        
        DIST = dict()
        for key in self.NODES:
            node = self.NODES[key]
            distance = node.getDistance()
            if distance >= 0:
                if self.__cut > 0 and distance <= self.__cut:
                    DIST[node.id] = distance
                elif self.__cut == 0:
                    DIST[node.id] = distance
        return DIST
    
    
    def shortest_path_all_distances(self, node1, cut=0):
        self.__cut = cut
        self.__initializeForSP()
        
        DIST = dict()
        for key in self.NODES:
            node = self.NODES[key]
            d = self.shortest_path_distance(node1, node, cut)
            if d != None and d >= 0:
                # print (d, node.id, node1.id)
                key = (node1.id, node.id)
                DIST[key] = d
        return DIST
    
    
    def plot(self, pcc = None, node1 = None, node2 = None):
        
        L = list(self.EDGES.items())
        for i in range(len(L)):
            edge = L[i][1]
            if edge.orientation == Edge.DOUBLE_SENS:
                plt.plot(edge.track.getX(), edge.track.getY(), '-', color="blue", linewidth = 0.5)
            else:
                plt.plot(edge.track.getX(), edge.track.getY(), '-', color="gray", linewidth = 0.5)

        '''
        for node in self.NODES:
            #print (str(len(node.getArcsEntrants())) + '-' + str(len(node.getArcsSortants()))) 
            plt.plot(node.coord.getX(), node.coord.getY(), 'gx', markersize=2)
            
        if pcc != None:
            X = pcc.getX()
            Y = pcc.getY()
            plt.plot(X, Y, '-', color="red", linestyle='--', dashes=(5, 10))
            
        if node1 != None:
            plt.plot(node1.coord.getX(), node1.coord.getY(), 'rx', markersize=5)
        if node2 != None:
            plt.plot(node2.coord.getX(), node2.coord.getY(), 'rx', markersize=5)
        '''
        plt.show()
        

    def fastPlot(self, edges='k-', nodes='', indirect='r-', size=0.5):
    
        x1d = []; y1d = []; x1i = []; y1i = []
        x2d = []; y2d = []; x2i = []; y2i = []
        exd = []; eyd = []; exi = []; eyi = [];
        nx = [];   ny = [];
        
        L = list(self.EDGES.items())
        for i in range(len(L)):
            edge = L[i][1]
            for j in range(edge.track.size()-1):
                if edge.orientation == Edge.DOUBLE_SENS:
                    x1d.append(edge.track.getX()[j]); x2d.append(edge.track.getX()[j+1])
                    y1d.append(edge.track.getY()[j]); y2d.append(edge.track.getY()[j+1])
                else:
                    x1i.append(edge.track.getX()[j]); x2i.append(edge.track.getX()[j+1])
                    y1i.append(edge.track.getY()[j]); y2i.append(edge.track.getY()[j+1])
            nx.append(edge.track.getX()[0]); nx.append(edge.track.getX()[-1])   
            ny.append(edge.track.getY()[0]); ny.append(edge.track.getY()[-1])

        for s, t, u, v in zip(x1d, y1d, x2d, y2d):
            exd.append(s); exd.append(u); exd.append(None)
            eyd.append(t); eyd.append(v); eyd.append(None)
        for s, t, u, v in zip(x1i, y1i, x2i, y2i):
            exi.append(s); exi.append(u); exi.append(None)
            eyi.append(t); eyi.append(v); eyi.append(None)
            
        if len(edges) > 0: 
            plt.plot(exd, eyd, edges, linewidth=size)
        if len(indirect) > 0: 
            plt.plot(exi, eyi, indirect, linewidth=size)
        if (len(nodes) > 0):
            plt.plot(nx, ny, nodes, markersize=4*size)        
            
    def bbox(self):
        '''
        BBOx sur edges

        Returns
        -------
        (xmin, xmax, ymin, ymax)
            bounding box on EDGES of network

        '''
        tarray_xmin = []
        tarray_xmax = []
        tarray_ymin = []
        tarray_ymax = []
        
        for key in self.EDGES:
            edge = self.EDGES[key]
            trace = edge.track
            tarray_xmin.append(trace.operate(Operator.MIN, 'x'))
            tarray_xmax.append(trace.operate(Operator.MAX, 'x'))
            tarray_ymin.append(trace.operate(Operator.MIN, 'y'))
            tarray_ymax.append(trace.operate(Operator.MAX, 'y'))
        
        xmin = Sum.co_min(tarray_xmin)
        xmax = Sum.co_max(tarray_xmax)
        ymin = Sum.co_min(tarray_ymin)
        ymax = Sum.co_max(tarray_ymax)
        
        return (xmin, xmax, ymin, ymax)


#if __name__ == '__main__':
#    n1 = Node()
#    n = Network()