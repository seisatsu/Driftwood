####################################
# Driftwood 2D Game Dev. Suite     #
# framemanager.py                  #
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

from ctypes import byref
from ctypes import c_int
from sdl2 import *

import filetype


class FrameManager:  # TODO: Move most of Area drawing logic into this manager.
    """The Frame Manager

    This class contains manages the current graphical frame. It allows manipulating and adding content to its workspace,
    which can then be copied onto the frame. Alternatively, a texture or ImageFile may be given to replace the current
    frame. WindowManager queries us for the current frame each tick.

    Attributes:
        driftwood: Base class instance.
        offset: Offset at which to draw the viewport.
        centering: Whether to center on the player in large areas.
        changed: Whether the frame has been changed. [STATE_NOTCHANGED, STATE_BACKBUFFER_NEEDS_UPDATE, STATE_CHANGED]
    """

    def __init__(self, driftwood):
        """FrameManager class initializer.

        Initializes frame handling.

        Args:
            driftwood: Base class instance.
        """
        # Mac OS X 10.9 with SDL 2.0.1 does double buffering and needs a second rendering of the same image on still frames.
        self.STATE_NOTCHANGED, self.STATE_BACKBUFFER_NEEDS_UPDATE, self.STATE_CHANGED = range(3)

        self.driftwood = driftwood
        self._frame = None  # [self.__texture, srcrect, dstrect]

        # Offset at which to draw the viewport.
        self.offset = [0, 0]

        # Whether to center on the player in large areas.
        self.centering = True

        self.__imagefile = None
        self.__texture = None
        self.__workspace = None

        self.changed = self.STATE_NOTCHANGED

    def prepare(self, width, height):
        """Prepare and clear the local workspace.

        Set up our workspace as a texture of the specified size. This also clears the workspace.

        Args:
            width: Width in pixels.
            height: Height in pixels.

        Returns:
            True if succeeded, False if failed.
        """
        if self.__workspace:
            SDL_DestroyTexture(self.__workspace) # TODO: Find out why this causes __build_frame to fail.

        self.__workspace = SDL_CreateTexture(self.driftwood.window.renderer,
                                             SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET,
                                             width, height)

        if type(self.__workspace) == int and self.__workspace < 0:
            self.driftwood.log.msg("ERROR", "Frame", "SDL", SDL_GetError())
            return False

        return True

    def frame(self, tex=None, zoom=False):
        """Replace the current frame with a texture or the internal workspace, and adjust the viewport accordingly.

        Args:
            tex: Use internal workspace if None, otherwise SDL_Texture or filetype.ImageFile instance.
            zoom: Whether or not to zoom the texture.

        Returns:
            True
        """
        # Use our internal workspace.
        if tex is None:
            self.__texture = self.__workspace

        # Prevent this ImageFile (probably from a script) from losing scope and taking our texture with it.
        elif isinstance(tex, filetype.ImageFile):
            if self.__imagefile and tex is not self.__imagefile:
                self.__imagefile._terminate()
            self.__imagefile = tex
            if self.__texture and self.__imagefile.texture is not self.__texture:
                SDL_DestroyTexture(self.__texture)
            self.__texture = self.__imagefile.texture

        # It's just an ordinary texture, probably passed from the engine code.
        else:
            if self.__texture and self.__texture is not tex:
                SDL_DestroyTexture(self.__texture)
            self.__texture = tex

        # Get texture width and height.
        tw, th = c_int(), c_int()
        SDL_QueryTexture(self.__texture, None, None, byref(tw), byref(th))
        tw, th = tw.value, th.value

        # Zoom the texture.
        if zoom:
            tw *= self.driftwood.config["window"]["zoom"]
            th *= self.driftwood.config["window"]["zoom"]

        # Both the dstrect and the window size are measured in logical
        # coordinates at this stage.  The transformation to physical
        # coordinates happens below in tick().

        # Set up viewport calculation variables.
        srcrect, dstrect = SDL_Rect(), SDL_Rect()
        srcrect.x, srcrect.y, srcrect.w, srcrect.h = 0, 0, tw, th
        dstrect.x, dstrect.y, dstrect.w, dstrect.h = 0, 0, tw, th

        # Get logical window width and height.
        ww = self.driftwood.window.logical_width
        wh = self.driftwood.window.logical_height

        # Area width is smaller than window width. Center by width on area.
        if tw < ww:
            dstrect.x = int(ww / 2 - tw / 2)

        # Area width is larger than window width. Center by width on player.
        if tw > ww and self.centering:
            if self.driftwood.entity.player:
                playermidx = self.driftwood.entity.player.x + (self.driftwood.entity.player.width / 2)
                prepx = int(ww / 2 - playermidx * self.driftwood.config["window"]["zoom"])

                if prepx > 0:
                    dstrect.x = 0
                elif prepx < ww - tw:
                    dstrect.x = ww - tw
                else:
                    dstrect.x = prepx

            else:
                dstrect.x = int(ww / 2 - tw / 2)

        # Area height is smaller than window height. Center by height on area.
        if th < wh:
            dstrect.y = int(wh / 2 - th / 2)

        # Area height is larger than window height. Center by height on player.
        if th > wh and self.centering:
            if self.driftwood.entity.player:
                playermidy = self.driftwood.entity.player.y + (self.driftwood.entity.player.height / 2)
                prepy = int(wh / 2 - playermidy * self.driftwood.config["window"]["zoom"])

                if prepy > 0:
                    dstrect.y = 0
                elif prepy < wh - th:
                    dstrect.y = wh - th
                else:
                    dstrect.y = prepy

            else:
                dstrect.y = int(wh / 2 - th / 2)

        # Adjust the viewport offset.
        dstrect.x += self.offset[0]
        dstrect.y += self.offset[1]

        # Adjust and copy the frame onto the viewport.
        self._frame = [self.__texture, srcrect, dstrect]

        # Mark the frame changed.
        self.changed = self.STATE_CHANGED

        return True

    def copy(self, tex, srcrect, dstrect):
        """Copy a texture onto the workspace.
        
        Copy the source rectangle from the texture tex to the destination rectangle in our workspace.
        
        Args:
            tex: Texture to copy.
            srcrect: Source rectangle [x, y, w, h]
            dstrect: Destination rectangle [x, y, w, h]
        
        Returns:
            True if succeeded, False if failed.
        """
        # We have to finish before we return.
        ret = True

        # Tell SDL to render to our workspace instead of the window's frame.
        r = SDL_SetRenderTarget(self.driftwood.window.renderer, self.__workspace)
        if r < 0:
            self.driftwood.log.msg("ERROR", "Frame", "SDL", SDL_GetError())
            ret = False

        # Set up the rectangles.
        src = SDL_Rect()
        dst = SDL_Rect()
        src.x, src.y, src.w, src.h = srcrect
        dst.x, dst.y, dst.w, dst.h = dstrect

        # Copy the texture onto the workspace.
        r = SDL_RenderCopy(self.driftwood.window.renderer, tex, src,
                           dst)
        if r < 0:
            self.driftwood.log.msg("ERROR", "Frame", "SDL", SDL_GetError())
            ret = False

        # Tell SDL to switch rendering back to the window's frame.
        r = SDL_SetRenderTarget(self.driftwood.window.renderer, None)
        if r < 0:
            self.driftwood.log.msg("ERROR", "Frame", "SDL", SDL_GetError())
            ret = False

        return ret

    def _terminate(self):
        """Cleanup before deletion.
        """
        if self.__texture:
            SDL_DestroyTexture(self.__texture)
            self.__texture = None
        if self._frame:
            SDL_DestroyTexture(self._frame[0])
            self._frame = None