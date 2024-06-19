import argparse
from abc import ABC, abstractmethod

class Scanner:
    def __init__(self, f, i, s):
        self._f = f
        self._i = i
        self._s = s

    def getIcon(self):
        icon_file = open('./configs/icon.yaml', 'r', encoding="utf-8")
        icon_lines = icon_file.readlines()
        icon = dict()

        for icon_line in icon_lines:
            icon_line = icon_line.strip().split(" ")
            if len(icon_line) == 4:
                icon[icon_line[0]] = [icon_line[2] if icon_line[2] != 'null' else "", icon_line[3] if icon_line[3] != 'null' else ""]

        if self._i in icon.keys():
            return icon[self._i]
        else:
            print('please use right icon name, the following is legal:')
            for icon_name in icon.keys():
                print(icon_name)
            exit(0)

    def getJson(self):
        yaml = open(self._f)
        lines = yaml.readlines()

        lines = [line.rstrip() + " " for line in lines]
        return lines

    def getStyle(self):
        return self._s


class DealJson:
    def __init__(self, f):
        self._row = 0
        self._col = 0
        self._f = f

    def getNextToken(self):

        cnt = 0
        buf = ""
        while self._row < len(self._f):
            while self._col < len(self._f[self._row]):
                if len(buf) == 0 and (self._f[self._row][self._col] == " " or self._f[self._row][self._col] == ","):
                    self._col += 1
                    continue
                if self._f[self._row][self._col] == "\'":
                    cnt += 1
                if cnt == 0:
                    if self._f[self._row][self._col] == "," or self._f[self._row][self._col] == " " or self._f[self._row][self._col] == ":":
                        if len(buf) > 0:
                            return buf
                        else:
                            buf = buf + self._f[self._row][self._col]
                            self._col += 1
                            return buf
                elif cnt == 2:
                    self._col += 1
                    return buf

                if self._f[self._row][self._col] == "\'":
                    self._col += 1
                    continue
                buf = buf + self._f[self._row][self._col]
                self._col += 1

            self._col = 0
            self._row += 1
        return ""


class Component(ABC):
    def __init__(self, name):
        self.name = name
        self.level = []

    @abstractmethod
    def draw(self, buf, interval, icon_type):
        pass


class Leaf(Component):
    def __init__(self, name):
        super(Leaf, self).__init__(name)

    def draw(self, buf, interval, icon_type):
        if self.name != 'null':
            buf[-1] += ": " + self.name


class Container(Component):
    def __init__(self, name, icon):
        super(Container, self).__init__(name)
        self.icon = icon

    def draw(self, buf, interval, icon_type):
        if self.name != 'null':
            buf.append(interval + icon_type + self.name)
        # for i in range(len(self.level)):
        #     if len(self.level[i].level) == 0 or (len(self.level[i].level) == 1 and len(self.level[i].level[0].level) == 0):
        #         self.level[i].draw(buf, interval + "  ", self.icon[1])
        #     else:
        #         self.level[i].draw(buf, interval + "  ", self.icon[0])


class IteratorBase(ABC):
    def __init__(self):
        self.pos = -1

    @abstractmethod
    def hasNext(self, root):
        pass

    @abstractmethod
    def next(self, root, buf, interval, icon_type):
        pass

    @abstractmethod
    def remove(self):
        pass


class LeafIterator(IteratorBase):
    def __init__(self):
        super(LeafIterator, self).__init__()

    def hasNext(self, root):
        if self.pos + 1 >= len(root.level) and self.pos + 1 != 0:
            return False
        return True

    def next(self, root, buf, interval, icon_type):
        if self.pos + 1 == 0:
            self.pos = self.pos + 1
        else:
            self.pos = (self.pos + 1) % len(root.level)
        if self.pos == 0:
            root.draw(buf, interval, icon_type)
        return root, interval, icon_type

    def remove(self):
        return None


class ContainerIterator(IteratorBase):
    def __init__(self):
        super(ContainerIterator, self).__init__()

    def hasNext(self, root):
        if self.pos + 1 >= len(root.level) and self.pos + 1 != 0:
            return False
        return True

    def next(self, root, buf, interval, icon_type):
        if self.pos == -1:
            root.draw(buf, interval, icon_type)
        if self.pos + 1 == 0:
            self.pos = self.pos + 1
        else:
            self.pos = (self.pos + 1) % len(root.level)
        if len(root.level[self.pos].level) == 0 or (len(root.level[self.pos].level) == 1 and len(root.level[self.pos].level[0].level) == 0):
            return root.level[self.pos], interval + "  ", root.icon[1]
        else:
            return root.level[self.pos], interval + "  ", root.icon[0]

    def remove(self):
        return None


class Shape(ABC):
    @abstractmethod
    def draw(self, buf):
        pass

    def strReplace(self, pos, ch, buf):
        if pos < len(buf) - 1:
            return buf[0:pos] + ch + buf[pos+1:]
        else:
            return buf[0:pos] + ch


class JsonTree(ABC):
    @abstractmethod
    def addJsonTreeType(self):
        pass

    @abstractmethod
    def createIterator(self):
        pass


class ContainerJsonTree(JsonTree):
    def addJsonTreeType(self):
        return None

    def getDraw(self):
        pass

    def createIterator(self):
        return ContainerIterator()


class LeafJsonTree(JsonTree):
    def addJsonTreeType(self):
        return None

    def getDraw(self):
        pass

    def createIterator(self):
        return LeafIterator()


class JsonTreeOutput:
    def __init__(self, root):
        self.root = root

    def output(self, buf, interval, icon_type):
        if len(self.root.level) == 0:
            iter = LeafJsonTree().createIterator()
        else:
            iter = ContainerJsonTree().createIterator()

        while iter.hasNext(self.root):
            oldRoot = self.root
            oldInterval = interval
            oldIcon_type = icon_type
            self.root, interval, icon_type = iter.next(self.root, buf, interval, icon_type)
            if self.root != oldRoot:
                self.output(buf, interval, icon_type)
            self.root = oldRoot
            interval = oldInterval
            icon_type = oldIcon_type


class Tree(Shape):
    def draw(self, buf):
        for i in range(len(buf)):
            pos = 0
            while pos + 2 < len(buf[i]):
                if buf[i][pos + 2] != ' ':
                    buf[i] = self.strReplace(pos, '└', buf[i])
                    buf[i] = self.strReplace(pos + 1, '─', buf[i])
                    for j in range(i - 1, -1, -1):
                        if buf[j][pos] == ' ':
                            buf[j] = self.strReplace(pos, '│', buf[j])
                        elif buf[j][pos] == '└':
                            buf[j] = self.strReplace(pos, '├', buf[j])
                            break
                        else:
                            break
                    break
                pos += 1


class Rectangle(Shape):
    def draw(self, buf):
        maxlen = 36
        for i in range(len(buf)):
            buf[i] += "─" * (maxlen - len(buf[i]))
            buf[i] = self.strReplace(len(buf[i])-1, '┤', buf[i])
            pos = 0
            while pos + 2 < maxlen:
                if buf[i][pos+2] != ' ':
                    buf[i] = self.strReplace(pos, '├', buf[i])
                    buf[i] = self.strReplace(pos+1, '─', buf[i])
                    break
                if i > 0 and (buf[i-1][pos] == '├' or buf[i-1][pos] == '│' or buf[i-1][pos ]== "┤"):
                    buf[i] = self.strReplace(pos, '│', buf[i])
                if i + 1 == len(buf):
                    buf[i] = self.strReplace(pos, '─', buf[i])
                pos += 1
        buf[0] = self.strReplace(0, '┌', buf[0])
        buf[0] = self.strReplace(len(buf[0])-1, '┐', buf[0])
        buf[-1] = self.strReplace(0, '└', buf[-1])
        buf[-1] = self.strReplace(len(buf[-1])-1, '┘', buf[-1])
        for i in range(maxlen):
            if buf[-1][i] == '├':
                buf[-1] = self.strReplace(i, '└', buf[-1])


class ShapeContext:
    def __init__(self, strategy):
        self.strategy = strategy

    def executeStrategy(self, buf):
        self.strategy.draw(buf)


class ShapeFactory(ABC):
    @abstractmethod
    def createShape(self):
        pass


class RectangleShapeFactory(ShapeFactory):
    def createShape(self):
        return Rectangle()


class TreeShapeFactory(ShapeFactory):
    def createShape(self):
        return Tree()


class JsonExplorer:
    def __init__(self, dealjson, icon):
        self.dealjson = dealjson
        self.root = Container("null", icon)
        self._load(self.root, icon)
        self.jsonContent = []
        JsonTreeOutput(self.root).output(self.jsonContent, "", " ")
        # self.root.draw(self.jsonContent, "", " ")

    def getJsonContent(self):
        return self.jsonContent

    def _load(self, farther, icon):
        buf = "none"
        cnt = 0
        while buf != "":
            buf = self.dealjson.getNextToken()
            if cnt == 0 and buf == "{":
                cnt += 1
                continue
            if cnt == 0:
                return buf
            if buf == "}" and cnt == 1:
                return ""
            operand = self.dealjson.getNextToken()
            if operand == ":":
                son = Container(buf, icon)
                val = self._load(son, icon)
                if val != "" and val != "null":
                    grandson = Leaf(val)
                    son.level.append(grandson)
                farther.level.append(son)
            else:
                print('invalid json file')
                exit(0)
        return ""


class JsonProduct:
    def getJsonExplorer(self, dealjson, icon):
        return JsonExplorer(dealjson, icon)

    def getShape(self, style):
        return eval(style[0].upper() + style[1:] + "ShapeFactory")().createShape()

    def getDealJson(self, f):
        return DealJson(f)


class AbstractJsonBuilder(ABC):
    @abstractmethod
    def buildJsonExplorer(self, dealjson, icon):
        pass

    @abstractmethod
    def buildShape(self, style):
        pass

    @abstractmethod
    def buildDealJson(self, f):
        pass


class JsonBuilder(AbstractJsonBuilder):
    def buildShape(self, style):
        return JsonProduct().getShape(style)

    def buildDealJson(self, f):
        return JsonProduct().getDealJson(f)

    def buildJsonExplorer(self, dealjson, icon):
        return JsonProduct().getJsonExplorer(dealjson, icon)


class JsonDirector:
    def __init__(self):
        self.shape = None
        self.dealJson = None
        self.jsonExplorer = None

    def constructJson(self, style, f, icon):
        self.shape = JsonBuilder().buildShape(style)
        self.dealJson = JsonBuilder().buildDealJson(f)
        self.jsonExplorer = JsonBuilder().buildJsonExplorer(self.dealJson, icon)
        self.shapeContext = ShapeContext(eval(style[0].upper() + style[1:])())

    def getJson(self):
        jsonContent = self.jsonExplorer.getJsonContent()
        # self.shape.draw(jsonContent)
        self.shapeContext.executeStrategy(jsonContent)
        return jsonContent


class FunnyJsonExplorer:
    def __init__(self, style, f, icon):
        self.jsonExplorer = JsonDirector()
        self.jsonExplorer.constructJson(style, f, icon)

    def show(self, icon):
        jsonContent = self.jsonExplorer.getJson()
        for line in jsonContent:
            print(line)

        if icon[0] != "" or icon[1] != "":
            print()
            print('poker-face-icon-family: 中间节点icon:', icon[0], "叶节点icon:", icon[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='./test.json', help='the json file to process')
    parser.add_argument('-s', '--style', default='tree', help='the style of json')
    parser.add_argument('-i', '--icon', default='default', help='middle icon, leaf icon')
    args = parser.parse_args()

    scanner = Scanner(args.file, args.icon, args.style)
    f = scanner.getJson()
    icon = scanner.getIcon()
    style = scanner.getStyle()

    fje = FunnyJsonExplorer(style, f, icon)
    buf = fje.show(icon)
