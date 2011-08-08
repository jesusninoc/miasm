#!/usr/bin/env python
#
# Copyright (C) 2011 EADS France, Fabrice Desclaux <fabrice.desclaux@eads.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import sys
import math
from PyQt4 import QtGui
from PyQt4 import QtCore


from PyQt4.Qt import QTextEdit
from PyQt4.Qt import QPlainTextEdit
from PyQt4.Qt import QMouseEvent
from PyQt4.Qt import QTextCursor
from PyQt4.Qt import QEvent
from PyQt4.Qt import Qt

app = None
from grandalf.graphs import *
from grandalf.layouts import SugiyamaLayout, VertexViewer
from grandalf.routing import *

from miasm.core import asmbloc
def __init__(self, w = 40, h = 40, data = None):
    self.w = w
    self.h = h
VertexViewer.__init__ = __init__

class HighlightingRule():
    def __init__( self, pattern, format ):
        self.pattern = pattern
        self.format = format


def gen_syntax_rules():
    highlightingRules = []
    number = QtGui.QTextCharFormat()
    label = QtGui.QTextCharFormat()
    my_id = QtGui.QTextCharFormat()
    highlight_word = QtGui.QTextCharFormat()


    # hex number
    brushg = QtGui.QBrush( Qt.green, Qt.SolidPattern )
    pattern = QtCore.QRegExp( "0x[0-9a-fA-F]+" )
    pattern.setMinimal( False )
    number.setForeground( brushg )
    rule = HighlightingRule( pattern, number )
    highlightingRules.append( rule )

    
    pattern = QtCore.QRegExp( "\b[0-9]+\b" )
    pattern.setMinimal( False )
    number.setForeground( brushg )
    rule = HighlightingRule( pattern, number )
    highlightingRules.append( rule )
    

    #label
    brushb = QtGui.QBrush( Qt.blue, Qt.SolidPattern )
    pattern = QtCore.QRegExp( "[0-9a-zA-Z_\.]+:$" )
    pattern.setMinimal( False )
    label.setForeground( brushb )
    rule = HighlightingRule( pattern, label )
    highlightingRules.append( rule )

    #label
    brushb = QtGui.QBrush( Qt.blue, Qt.SolidPattern )
    pattern = QtCore.QRegExp( "[0-9a-zA-Z_\.]+:" )
    pattern.setMinimal( False )
    my_id.setForeground( brushb )
    rule = HighlightingRule( pattern, my_id )
    highlightingRules.append( rule )

    return highlightingRules


syntax_rules = gen_syntax_rules()


class MyHighlighter( QtGui.QSyntaxHighlighter ):
    def __init__( self, parent ):
        QtGui.QSyntaxHighlighter.__init__( self, parent )
        self.parent = parent


        self.highlightingRules = syntax_rules





    def highlightBlock( self, text ):
        for rule in self.highlightingRules:
            expression = QtCore.QRegExp( rule.pattern )
            index = expression.indexIn( text )
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat( index, length, rule.format )
                index = text.indexOf( expression, index + length )
        self.setCurrentBlockState( 0 )


border_l = 10
font_w = 7
font_h = 16
scale_x = 20.6#2.5
scale_y = 20.6#2.5

title_h = font_h
font_size = 8

zoom_lvl = 1.0
pan_lvl = 120

mfont = QtGui.QFont("Monospace", 8)


def getTextwh(txt):
    l = txt.split('\n')
    h = len(l)
    w = max(map(lambda x:len(x), l))
    return w, h


def getTextwh_font(txt, zoom, font):
    l = txt.split('\n')
    max_c = max(map(lambda x:len("X"+x+"X"), l))
    w_max = -1

    r  = QtGui.QFontMetrics(font).boundingRect(QtCore.QRect(), 0, txt)
    w_max, h_max = r.width(), r.height()
    return w_max+30, h_max+20+len(l)*1


class graph_edge(QtGui.QGraphicsItem):
    def __init__(self, min_x, min_y, max_x, max_y, pts, color, end_angle, my_splines):
        QtGui.QGraphicsItem.__init__(self)
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.pts = pts
        self.color = color
        self.setZValue(-1)
        self.end_angle = end_angle
        self.my_splines = my_splines
    def boundingRect(self):
        return QtCore.QRectF(self.min_x, self.min_y, self.max_x, self.max_y)

    def paint(self, painter, option, unused_widget):
        painter.setPen(self.color)
        brush = QtGui.QBrush(self.color)
        brush.setStyle(QtCore.Qt.SolidPattern)
        painter.setBrush(brush)
                       
        for i, p1 in enumerate(self.pts[:-1]):
            p2 = self.pts[i+1]
            painter.drawLine(*(p1 + p2))
    
        a = -self.end_angle-math.pi
        d_a = 0.3
        p3 = p2[0]+10*math.cos(a-d_a), p2[1]-10*math.sin(a-d_a)
        p4 = p2[0]+10*math.cos(a+d_a), p2[1]-10*math.sin(a+d_a)
        p5 = p2


        painter.drawPolygon(QtCore.QPoint(*p2), QtCore.QPoint(*p3), QtCore.QPoint(*p4), QtCore.QPoint(*p5) )
    
class node_asm_bb(QTextEdit):
    def __init__(self, txt, mainwin):
        self.txt = txt
        self.mainwin = mainwin
        QTextEdit.__init__(self)
        self.setText(self.txt)
        self.setFont(mfont)
        self.setReadOnly(True)





    def setpos(self, x, y, w, h):
        self.p_x = x
        self.p_y = y
        self.p_w = w
        self.p_h = h

        self.setFixedWidth(self.p_w)
        self.setFixedHeight(self.p_h)

        self.move(self.p_x, self.p_y)
        self.setFont(mfont)
        self.setCurrentFont(mfont)


    def get_word_under_cursor(self):
        cursor = self.textCursor()
        cursor.clearSelection()
        a, b = cursor.selectionStart () , cursor.selectionEnd ()
        print a, b
        #if only click, get word
        cut_char = [' ', "\t", "\n"]
        if a == b:
            while not self.txt[a] in cut_char:
                a-=1
                if a <0:
                    break
            a +=1
            
            while b <len(self.txt) and not self.txt[b] in cut_char:
                b+=1
        print a, b
        print self.txt[a:b]
        w = self.txt[a:b]
        return w

    def mousePressEvent(self, event):

        if event.button() == Qt.RightButton:
            # Rewrite the mouse event to a left button event so the cursor is
            # moved to the location of the pointer.
            event = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)

        QTextEdit.mousePressEvent(self, event)
        cursor = self.textCursor()
        

    def mouseDoubleClickEvent(self,mouseEvent):
        print "DOUBLE"
        w = self.get_word_under_cursor()
        app.postEvent(self.mainwin,MyEvent(w))

    def contextMenuEvent(self, event):
        global app
        w = self.get_word_under_cursor()
        menu = QtGui.QMenu(self)
        goto_ad = menu.addAction("sel: "+w)
        goto_ad.triggered.connect(lambda:app.postEvent(self.mainwin,MyEvent(w)))
        
        menu.addAction("Copy")
        menu.addAction("Paste")
        menu.exec_(event.globalPos())
    
    def paintEvent(self, e):
        if self.mainwin.view.graphicsView.zoom > -600:
            QTextEdit.paintEvent(self, e)
        
        


class View(QtGui.QFrame):

    def __init__(self, name, parent=None):
        QtGui.QFrame.__init__(self, parent)

        self.setFrameStyle(QtGui.QFrame.Sunken | QtGui.QFrame.StyledPanel)

        self.graphicsView= myQGraphicsView(parent)
        self.graphicsView.setRenderHint(QtGui.QPainter.Antialiasing, False)
        self.graphicsView.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.graphicsView.setViewportUpdateMode(
            QtGui.QGraphicsView.SmartViewportUpdate)

        size = self.style().pixelMetric(QtGui.QStyle.PM_ToolBarIconSize)
        iconSize = QtCore.QSize(size, size)

        # Label layout
        labelLayout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel(name)
        self.antialiasButton = QtGui.QToolButton()
        self.antialiasButton.setText("Antialiasing")
        self.antialiasButton.setCheckable(True)
        self.antialiasButton.setChecked(False)

        # No openGlButton
        # No printButton

        labelLayout.addWidget(self.label)
        labelLayout.addStretch()
        labelLayout.addWidget(self.antialiasButton)

        topLayout = QtGui.QGridLayout()
        topLayout.addLayout(labelLayout, 0, 0)
        topLayout.addWidget(self.graphicsView, 1, 0)
        self.setLayout(topLayout)

        self.connect(self.antialiasButton, QtCore.SIGNAL("toggled(bool)"),
                     self.toggleAntialiasing)
        self.setupMatrix()

    def view(self):
        return self.graphicsView

    def resetView(self):
        self.setupMatrix()
        self.graphicsView.ensureVisible(QtCore.QRectF(0, 0, 0, 0))

    def setupMatrix(self):
        scale = pow(2.0, 0)

        matrix = QtGui.QMatrix()
        matrix.scale(scale, scale)

        self.graphicsView.setMatrix(matrix)

    def toggleAntialiasing(self):
        self.graphicsView.setRenderHint(QtGui.QPainter.Antialiasing,
                                        self.antialiasButton.isChecked())


class myQGraphicsView(QtGui.QGraphicsView):
    def __init__(self, mainwin):
        QtGui.QGraphicsView.__init__(self)
        self.view = None
        self.i_pos = None
        self.in_move = False
        self.key_ctrl = False
        self.zoom = 1.0
        self.ty = 0.0
        self.mainwin = mainwin

        
        self.current_node = None
        

    def set_view(self, view):
        self.view = view
    def mouseMoveEvent(self, mouseEvent):
        if not self.in_move:
            QtGui.QGraphicsView.mouseMoveEvent(self, mouseEvent)

            return
        pt = mouseEvent.pos()
        x,y = pt.x(), pt.y()

        diff_x, diff_y = self.i_pos[0] - x, self.i_pos[1] - y 
        scroll_v =     self.verticalScrollBar()
        scroll_h =     self.horizontalScrollBar()


        pos_v = scroll_v.value()
        pos_h = scroll_h.value()

        pos_h += diff_x
        pos_v += diff_y

        scroll_v.setValue(pos_v)
        scroll_h.setValue(pos_h)
        self.i_pos = x, y

    def mousePressEvent(self, mouseEvent):

        QtGui.QGraphicsView.mousePressEvent(self, mouseEvent)
        if mouseEvent.button() == QtCore.Qt.LeftButton :
            pt = mouseEvent.pos()
            i = self.itemAt(pt)
            if not i or isinstance(i, graph_edge):
                x,y = pt.x(), pt.y()
                self.i_pos = x, y
                self.in_move = True
            elif isinstance(i, QtGui.QGraphicsProxyWidget) and isinstance(i.widget(), node_asm_bb):
                #if another node has selected text
                #clear it
                if self.current_node:
                    cursor = self.current_node.textCursor()
                    cursor.clearSelection()
                    self.current_node.setTextCursor(cursor)
                self.current_node = i.widget()




    def mouseReleaseEvent(self, mouseEvent):
        QtGui.QGraphicsView.mouseReleaseEvent(self, mouseEvent)
        if mouseEvent.button() == QtCore.Qt.LeftButton :
            self.in_move = False


    def keyPressEvent( self, event ):
        key = event.key()
        print "press", hex(key)
        if key == 0x1000021: #ctrl
            self.key_ctrl = True


        elif key == 0x1000005: #enter
            if self.mainwin.history_cur < len(self.mainwin.history_ad)-1:
                self.mainwin.history_cur +=1
            app.postEvent(self.mainwin,MyEvent(self.mainwin.history_ad[self.mainwin.history_cur]))
            
        elif key == 0x1000000: #esc
            if self.mainwin.history_cur>0:
                self.mainwin.history_cur -= 1
            app.postEvent(self.mainwin,MyEvent(self.mainwin.history_ad[self.mainwin.history_cur]))

        elif self.key_ctrl and key in  [43, 45]: # - +
            if key == 43:
                self.zoom +=100
            elif key == 45:
                self.zoom -=100
            scale = pow(2.0, (self.zoom /600.0))
            matrix = QtGui.QMatrix()
            matrix.scale(scale, scale)
            
            self.setMatrix(matrix)
            
        elif key in [0x1000012, 0x1000014]:
            if key == 0x1000012:
                diff_x = 20
            else:
                diff_x = -20
            scroll_h =     self.horizontalScrollBar()            
            pos_h = scroll_h.value()
            pos_h += diff_x
            scroll_h.setValue(pos_h)

        elif key in [0x1000013, 0x1000015]:
            if key == 0x1000013:
                diff_y = -20
            else:
                diff_y = 20
            scroll_v =     self.verticalScrollBar()            
            pos_v = scroll_v.value()
            pos_v += diff_y
            scroll_v.setValue(pos_v)

    def keyReleaseEvent( self, event ):
        key = event.key()
        print "relea", hex(key)
        if key == 0x1000021: #ctrl
            self.key_ctrl = False

    def wheelEvent(self, event):
        #XXX bug if maximize win
        mp_x, mp_y = event.pos().x(), event.pos().y()
        delta = event.delta()

        scroll_v =     self.verticalScrollBar()



        if self.key_ctrl:
            self.zoom +=delta
        else:
            pos_v = scroll_v.value()
            pos_v -= delta  
            scroll_v.setValue(pos_v)


        scale = pow(2.0, (self.zoom /600.0))
        matrix = QtGui.QMatrix()
        matrix.scale(scale, scale)

        self.setMatrix(matrix)





class MainWindow(QtGui.QWidget):

    def __init__(self, ad = None, all_bloc = [], label = False, dis_callback = None):
        QtGui.QWidget.__init__(self, parent = None)

        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.close)
        self.label = label
        self.ad = ad
        self.all_bloc = all_bloc
        self.dis_callback = dis_callback
        self.history_ad = []
        self.history_cur = -1

        view = View("Graph view", self)
        self.view = view

        self.populateScene(ad, all_bloc)

        view.view().setScene(self.scene)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(view)
        self.setLayout(layout)

        self.setWindowTitle("Miasm Disasm")


        self.i_pos = None
        self.drop_mouse_event = False
        


    def pos2graphpos(self, x, y):
        o_x = self.zoom*x + self.add_x
        o_y = self.zoom*y + self.add_y
        return o_x, o_y
    def graphpos2pos(self, x, y):
        o_x = (x-self.add_x)/self.zoom
        o_y = (y-self.add_y)/self.zoom
        return o_x, o_y

    def auto_zoom(self):
        if self.max_x == self.min_x:
            z1 = 1
        else:
            z1 = self.size().width()/(self.max_x - self.min_x)
        if self.max_y == self.min_y:
            z2 = 1
        else:
            z2 = self.size().height()/(self.max_y - self.min_y)

        self.zoom = min(z1, z2)
        self.zoom = max(0.1, self.zoom)
        #self.zoom*=0.8
        self.zoom_l = math.log(self.zoom)

        print self.min_x
        print self.min_y
        print self.max_x
        print self.max_y

        self.add_x = self.size().width()/2.0 - ((self.max_x+self.min_x)/2.0) * self.zoom
        self.add_y = self.size().height()/2.0 - ((self.max_y+self.min_y)/2.0) * self.zoom

        print self.zoom
        print self.add_x, self.add_y
        for e in self.editor.values():
            e.zoom(self.zoom)




    def graph_from_asmbloc(self, ad, all_bloc):
        V = {}
        E = []
        for b in all_bloc:
            if self.label:
                V[b.label] = Vertex(str(b.label.name) +":\n"+"\n".join(["%.8X  "%x.offset + str(x) for x in b.lines]))
            else:
                V[b.label] = Vertex(str(b.label.name) +":\n"+"\n".join([str(x) for x in b.lines]))
        for b in all_bloc:
            for c in b.bto:
                if not isinstance(c.label, asmbloc.asm_label):
                    continue
                data = QtCore.Qt.black
                if c.c_t == asmbloc.asm_constraint.c_to:
                    if b.lines and b.lines[-1].splitflow():
                        data = QtCore.Qt.green
                    else:
                        data = QtCore.Qt.blue
                else:
                    data = QtCore.Qt.red
                ###
                if b.label in V and c.label in V:
                    E.append(Edge(V[b.label], V[c.label], data = data))
        h = asmbloc.getblocby_offset(all_bloc, ad)
        if h:
            hdr = V[h.label]
        else:
            hdr = None
        V =  V.values()
        g = Graph(V,E)
        return hdr, g, V, E
        
    def graph_from_v_e(self, ad, all_bloc):
        v_hdr, v_dct, edges = all_bloc
        V = {}
        E = []
        for v_id, c in v_dct.items():
            V[v_id] = Vertex(str(c))
        for a, b in edges:
            data = QtCore.Qt.black
            E.append(Edge(V[a], V[b], data = data))
        hdr = V[v_hdr]
        V =  V.values()
        g = Graph(V,E)

        
        return hdr, g, V, E


    def add_new_bloc(self, ad, all_bloc = []):
        print 'add_new_bloc', ad
        if isinstance(ad, str):
            if ad.startswith('loc_'):
                ad = int(ad[4:12], 16)
            elif ad.startswith('0x'):
                ad = int(ad, 16)
            else:
                print 'BAD AD'
                return
        #print hex(ad)

        if not self.history_ad or (self.history_cur == len(self.history_ad)-1 and ad != self.history_ad[-1]):
            print 'add hist'
            self.history_ad.append(ad)
            self.history_cur +=1
        

        print "AD", hex(ad)

        for b in self.scene_blocs:
            b.widget().destroy()
            self.scene.removeItem(b)
        self.scene_blocs = []
        for e in self.scene_edges:
            self.scene.removeItem(e)
        self.scene_edges = []
        self.scene.clear()

        if not all_bloc:
            print 'DIS', hex(ad)
            all_bloc = self.dis_callback(ad)
            g = asmbloc.bloc2graph(all_bloc)
            open("graph.txt" , "w").write(g)


        if isinstance(all_bloc, list):
            hdr, g, V, E = self.graph_from_asmbloc(ad, all_bloc)
        else:
            hdr, g, V, E = self.graph_from_v_e(ad, all_bloc)
        index = 0

        print 'g ok'
        print 'vertex: ', len(g.C), len(g.C[index].sV), 'edges:', len(g.C[index].sE)
        print 'hdr', hdr
        
        nn = node_asm_bb("toto", self)
        mfont = nn.currentFont()
        class defaultview(object):
            def __init__(self, data = None):
                self.data = data
                if not data:
                    self.w, self.h = 80,40
                else:
                    self.data = self.data.replace('\t', ' '*4)
                    s = self.data.split('\n')
                    w, h = getTextwh_font(self.data, 1, mfont)
                    self.h = h
                    self.w = w

            self.l = []
            l = []
            def setpath(self, l):
                self.l = l
        for v in V: v.view = defaultview(v.data)
        for e in E: e.view = defaultview()
        min_x = None
        min_y = None
        max_pos_x = 0
        max_pos_y = 0

        for index in xrange(len(g.C)):

            gr = g.C[index]
            
            if False:#dr  and hdr in g.C[index].sV:
                r = [hdr]
            else:
                r = filter(lambda x: len(x.e_in())==0, gr.sV)
                if not r:
                    print 'no roots!'
                    r = [gr.sV.o[0]]
            r.sort()
            
            L = g.C[index].get_scs_with_feedback(r)
    
            sug = SugiyamaLayout(g.C[index])
            sug.xspace = 40
            sug.yspace = 40
    
            sug.init_all(roots=r,inverted_edges=filter(lambda x:x.feedback, g.C[index].sE))
            sug.route_edge = route_with_nurbs
            sug.draw(1)

            min_pos_x = None
            #compute min pos x
            for n in g.C[index].sV:
                pos = n.view.xy
                if min_pos_x == None or pos[0] - n.view.w/2 < min_pos_x:
                    min_pos_x = pos[0]- n.view.w/2
    

            new_max_pos_x = max_pos_x
            first_pos = None
            for n in g.C[index].sV:
                pos = n.view.xy
                if not first_pos:
                    first_pos = pos
                
                e = node_asm_bb(n.data, self)
                e.h = MyHighlighter(e)
                p_x = pos[0] - n.view.w/2 + max_pos_x - min_pos_x
                p_y = pos[1] - n.view.h/2
                e.setpos(p_x, p_y, n.view.w, n.view.h)
                if p_x + n.view.w > new_max_pos_x:
                    new_max_pos_x = p_x + n.view.w
                wproxy = self.scene.addWidget(e)
                self.scene_blocs.append(wproxy)
    
                e.show()
    
            for e in g.C[index].sE:
                min_x = None
                min_y = None
                max_x = None
                max_y = None
                end_angle = None
                try:
                    end_angle = e.view.head_angle
                except:
                    pass
                if not  e.view.l:
                    p1 = e.v[0].view.xy
                    p2 = e.v[1].view.xy

                    
                    for p in [p1, p2]:
                        if min_x == None or p[0] < min_x:
                            min_x = p[0]
                        if max_x == None or p[0] > max_x:
                            max_x = p[0]
    
                        if min_y == None or p[1] < min_y:
                            min_y = p[1]
                        if max_y == None or p[1] > max_y:
                            max_y = p[1]
                    pts = [p1, p2]
                else:
                    for p in e.view.l:
                        x, y = p[0] + max_pos_x, p[1]
                        p = x, y

                        if min_x == None or p[0] < min_x:
                            min_x = p[0]
                        if max_x == None or p[0] > max_x:
                            max_x = p[0]
    
                        if min_y == None or p[1] < min_y:
                            min_y = p[1]
                        if max_y == None or p[1] > max_y:
                            max_y = p[1]
                    pts = e.view.l
                for i, p in enumerate(pts):
                    x, y = p[0] + max_pos_x - min_pos_x, p[1]
                    p = x, y
                    pts[i] = p
                e = graph_edge(min_x, min_y, max_x, max_y, pts, e.data, end_angle, e.view.splines)
                
                self.scene.addItem(e)
                self.scene_edges.append(e)

            max_pos_x = new_max_pos_x

    
        if first_pos:
            self.view.view().centerOn(first_pos[0], first_pos[1])

        

    def populateScene(self, ad, all_bloc):
        self.scene = QtGui.QGraphicsScene()
        self.scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(230, 250, 250, 255)))
        self.scene_blocs = []
        self.scene_edges = []

        self.add_new_bloc(ad, all_bloc)
        self.ad = ad

    def customEvent(self,event):
        self.add_new_bloc(event.ad)
        

class MyEvent(QEvent):
    """ """
 
    def __init__(self,ad):
        """ """
        QEvent.__init__(self,QEvent.User)
        self.ad = ad


def graph_blocs(ad, all_bloc, label = False, dis_callback = None):
    global app
    app = QtGui.QApplication(sys.argv)
    g = MainWindow(ad, all_bloc, label, dis_callback)
    g.show()
    app.exec_()
    app.quit()
    app = None