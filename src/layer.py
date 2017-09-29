####################################
# Driftwood 2D Game Dev. Suite     #
# layer.py                         #
# Copyright 2014 PariahSoft LLC    #
# Copyright 2017 Michael D. Reiley #
# & Paul Merrill                   #
####################################

# **********
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
# **********

from typing import Dict, Optional

import tile
import tilemap


class Layer:
    """This class abstracts a layer.

    Attributes:
        tilemap: Parent Tilemap instance.

        properties: A dictionary containing layer properties.

        tiles: The list of Tile class instances for each tile.
    """

    def __init__(self, driftwood, tilemap: 'tilemap.Tilemap', layerdata: dict, zpos: int):
        """Layer class initializer.

        Args:
            driftwood: Base class instance.
            tilemap: Link back to the parent Tilemap instance.
            layerdata: JSON layer segment.
            zpos: Layer's z-position.
        """
        self.driftwood = driftwood
        self.tilemap = tilemap

        self.zpos = zpos
        self.properties = {}

        self.tiles = []

        # This contains the JSON of the layer.
        self.__layer = layerdata

        self.__prepare_layer()

    def __getitem__(self, item: int) -> '_AbstractColumn':
        return _AbstractColumn(self, item)

    def clear(self) -> None:
        for tile in self.tiles:
            tile.unregister()

    def tile(self, x: int, y: int) -> Optional['tile.Tile']:
        """Retrieve a tile from the layer by its coordinates.

        Args:
            x: x-coordinate
            y: y-coordinate

        Returns: Tile instance or None if out of bounds.
        """
        # Input Check
        try:
            CHECK(x, int)
            CHECK(y, int)
        except CheckFailure as e:
            self.driftwood.log.msg("ERROR", "Layer", self.zpos, "tile", "bad argument", e)
            return None

        if x < 0 or y < 0 or x >= self.tilemap.width or y >= self.tilemap.height:
            return None

        if int((y * self.tilemap.width) + x) < len(self.tiles):
            return self.tiles[int((y * self.tilemap.width) + x)]

        else:
            self.driftwood.log.msg("WARNING", "Layer", self.zpos, "tile",
                                   "tried to lookup nonexistent tile at", "{0}x{1}".format(x, y))
            return None

    def tile_index(self, x: int, y: int) -> Optional[int]:
        """Retrieve the index of a tile in the tiles list so you can modify it.

        Args:
            x: x-coordinate
            y: y-coordinate

        Returns: index of tile in tiles list if succeeded, None if failed.
        """
        # Input Check
        try:
            CHECK(x, int)
            CHECK(y, int)
        except CheckFailure as e:
            self.driftwood.log.msg("ERROR", "Layer", self.zpos, "tile_index", "bad argument", e)
            return None

        if int((y * self.tilemap.width) + x) < len(self.tiles):
            return int((y * self.tilemap.width) + x)

        else:
            self.driftwood.log.msg("WARNING", "Layer", self.zpos, "tile_index",
                                   "tried to lookup nonexistent tile at", "{0}x{1}".format(x, y))
            return None

    def _process_objects(self, objdata: dict) -> None:
        """Process and merge an object layer into the tile layer below.

        This method is marked private even though it's called from Tilemap, because it should not be called outside the
        engine code.

        Args:
            objdata: JSON object layer segment.
        """
        if "properties" in objdata:
            self.properties.update(objdata["properties"])

        for obj in objdata["objects"]:
            # Is the object properly sized?
            if (obj["x"] % self.tilemap.tilewidth or obj["y"] % self.tilemap.tileheight or
                    obj["width"] % self.tilemap.tilewidth or obj["height"] % self.tilemap.tileheight):
                self.driftwood.log.msg("ERROR", "Layer", self.zpos, "_process_objects",
                                       "invalid object size or placement")
                continue

            # Map object properties onto their tiles.
            for x in range(0, obj["width"] // self.tilemap.tilewidth):
                for y in range(0, obj["height"] // self.tilemap.tileheight):
                    tx = obj["x"] // self.tilemap.tilewidth + x
                    ty = obj["y"] // self.tilemap.tileheight + y

                    # Insert the object properties.
                    if "properties" in obj:
                        self.__expand_properties(obj["properties"])
                        self.tile(tx, ty).properties.update(obj["properties"])

                    # Set nowalk if present.
                    if "nowalk" in self.tile(tx, ty).properties:
                        self.tile(tx, ty).nowalk = self.tile(tx, ty).properties["nowalk"]

                    # Set exit if present.
                    for exittype in ["exit", "exit:up", "exit:down", "exit:left", "exit:right"]:
                        if exittype in self.tile(tx, ty).properties:

                            # First check for and handle wide exits.
                            exit_coords = self.tile(tx, ty).properties[exittype].split(',')
                            if len(exit_coords) != 4:
                                self.driftwood.log.msg("ERROR", "Layer", self.zpos, "_process_objects",
                                                       "invalid exit trigger",
                                                       self.tile(tx, ty).properties[exittype])
                                continue

                            if (exit_coords[2] and exit_coords[2][-1] == '+') and \
                                    (exit_coords[3] and exit_coords[3][-1] == '+'):  # Invalid wide exit.
                                self.driftwood.log.msg("ERROR", "Layer", "_process_objects",
                                                       "cannot have multi-directional wide exits")

                            # Check for and handle horizontal wide exit.
                            elif exit_coords[2] and exit_coords[2][-1] == '+':
                                base_coord = int(exit_coords[2][:1])  # Chop off the plus sign.
                                if tx % self.tilemap.width == base_coord:  # This is the first position.
                                    for wx in range(0, (obj["width"] // self.tilemap.tilewidth)):  # Set exits.
                                        final_coords = exit_coords
                                        final_coords[2] = str(base_coord + wx)
                                        self.tile(tx + wx, ty).exits[exittype] = ','.join(final_coords)
                                else:  # This is not the first position, skip.
                                    continue

                            # Check for and handle vertical wide exit.
                            elif exit_coords[3] and exit_coords[3][-1] == '+':
                                base_coord = int(exit_coords[3][:1])  # Chop off the plus sign.
                                if ty == base_coord:  # This is the first position.
                                    for wy in range(0, (obj["height"] // self.tilemap.tileheight)):  # Set exits.
                                        final_coords = exit_coords
                                        final_coords[3] = str(base_coord + wy)
                                        self.tile(tx, ty + wy).exits[exittype] = ','.join(final_coords)
                                else:  # This is not the first position, skip.
                                    continue

                            else:  # Just a regular exit.
                                self.tile(tx, ty).exits[exittype] = self.tile(tx, ty).properties[exittype]

                    # Handle entity auto-spawn triggers.
                    if "entity" in self.tile(tx, ty).properties:
                        args = self.tile(tx, ty).properties["entity"].split(",")
                        if len(args) != 4:
                            self.driftwood.log.msg("ERROR", "Layer", self.zpos, "_process_objects",
                                                   "invalid entity trigger",
                                                   self.tile(tx, ty).properties["entity"])
                            return
                        args[1] = int(args[1])
                        args[2] = int(args[2])
                        args[3] = int(args[3])
                        self.driftwood.entity.insert(*args)

    def __expand_properties(self, properties: Dict[str, str]) -> None:
        new_props = {}
        old_props = []

        # Expand user-defined trigger shortcuts
        for property_name in properties:
            if self.driftwood.script.is_custom_trigger(property_name):
                property = properties[property_name]
                event, trigger = self.driftwood.script.lookup(property_name, property)
                new_props[event] = trigger
                old_props.append(property_name)

        for event in new_props:
            properties[event] = new_props[event]
        for prop in old_props:
            del properties[prop]

    def __prepare_layer(self) -> None:
        # Set layer properties if present.
        if "properties" in self.__layer:
            self.properties = self.__layer["properties"]

        # Iterate through the tile graphic IDs.
        for seq, gid in enumerate(self.__layer["data"]):
            # Does this tile actually exist?
            if gid:
                # Find which tileset the tile's graphic is in.
                for ts in self.tilemap.tilesets:
                    if gid in range(*ts.range):
                        # Create the Tile instance for this tile.
                        self.tiles.append(tile.Tile(self, seq, ts, gid))

            # No tile, here create a dummy tile.
            else:
                self.tiles.append(tile.Tile(self, seq, None, None))

    def _terminate(self) -> None:
        """Cleanup before deletion.
        """
        for tile in self.tiles:
            tile._terminate()
        self.tiles = []


class _AbstractColumn:
    def __init__(self, layer: Layer, x: int):
        self.__layer = layer
        self.__x = x

    def __getitem__(self, item: int) -> Optional['tile.Tile']:
        return self.__layer.tile(self.__x, item)
