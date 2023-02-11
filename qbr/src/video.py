#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ts=4 sw=4 et

import cv2
from colordetection import color_detector
from config import config
from helpers import get_next_locale
import i18n

from constants import (
    COLOR_PLACEHOLDER,
    CUBE_SAVED_STATE,
    LOCALES,
    RESET_CUBE_KEY,
    ROOT_DIR,
    CUBE_PALETTE,
    MINI_STICKER_AREA_TILE_SIZE,
    MINI_STICKER_AREA_TILE_GAP,
    MINI_STICKER_AREA_OFFSET,
    SOLVE_CUBE_KEY,
    STICKER_AREA_TILE_SIZE,
    STICKER_AREA_TILE_GAP,
    STICKER_AREA_OFFSET,
    STICKER_CONTOUR_COLOR,
    CALIBRATE_MODE_KEY,
    SWITCH_LANGUAGE_KEY,
    TEXT_SIZE,
    E_INCORRECTLY_SCANNED,
    E_ALREADY_SOLVED
)

class Webcam:

    def reset(self):
        self.result_state = {}

        self.snapshot_state = [(255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255)]
        self.preview_state  = [(255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255)]
        self.calib_next = False

    def __init__(self, qbr):
        print('Starting webcam... (this might take a while, please be patient)')
        self.cam = cv2.VideoCapture(2)
        if not self.cam.isOpened():
            print("Cannot open camera")
            exit()
        print('Webcam successfully started')
        
        self.qbr = qbr

        self.colors_to_calibrate = ['green', 'red', 'blue', 'orange', 'white', 'yellow']
        self.average_sticker_colors = {}
        self.result_state = {}

        self.snapshot_state = [(255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255)]
        self.preview_state  = [(255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255)]
        self.calib_next = False                               

        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.calibrate_mode = False
        self.calibrated_colors = {}
        self.current_color_to_calibrate_index = 0
        self.done_calibrating = False

        saved_shot = config.get_setting(CUBE_SAVED_STATE, None)

        if saved_shot is not None:
            self.result_state = saved_shot

    def draw_stickers(self, frame, stickers, offset_x, offset_y):
        """Draws the given stickers onto the given frame."""
        index = -1
        for row in range(3):
            for col in range(3):
                index += 1
                x1 = (offset_x + STICKER_AREA_TILE_SIZE * col) + STICKER_AREA_TILE_GAP * col
                y1 = (offset_y + STICKER_AREA_TILE_SIZE * row) + STICKER_AREA_TILE_GAP * row
                x2 = x1 + STICKER_AREA_TILE_SIZE
                y2 = y1 + STICKER_AREA_TILE_SIZE

                # shadow
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 0),
                    -1
                )

                # foreground color
                cv2.rectangle(
                    frame,
                    (x1 + 1, y1 + 1),
                    (x2 - 1, y2 - 1),
                    color_detector.get_prominent_color(stickers[index]),
                    -1
                )

    def draw_preview_stickers(self, frame):
        """Draw the current preview state onto the given frame."""
        self.draw_stickers(frame, self.preview_state, STICKER_AREA_OFFSET, STICKER_AREA_OFFSET)

    def draw_snapshot_stickers(self, frame):
        """Draw the current snapshot state onto the given frame."""
        y = STICKER_AREA_TILE_SIZE * 3 + STICKER_AREA_TILE_GAP * 2 + STICKER_AREA_OFFSET * 2
        self.draw_stickers(frame, self.snapshot_state, STICKER_AREA_OFFSET, y)

    def find_contours(self, dilatedFrame):
        """Find the contours of a 3x3x3 cube."""
        contours, hierarchy = cv2.findContours(dilatedFrame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        final_contours = []

        # Step 1/4: filter all contours to only those that are square-ish shapes.
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            if len (approx) == 4:
                area = cv2.contourArea(contour)
                (x, y, w, h) = cv2.boundingRect(approx)

                # Find aspect ratio of boundary rectangle around the countours.
                ratio = w / float(h)

                # Check if contour is close to a square.
                if ratio >= 0.8 and ratio <= 1.2 and w >= 30 and w <= 60 and area / (w * h) > 0.4:
                    final_contours.append((x, y, w, h))

        # Return early if we didn't found 9 or more contours.
        if len(final_contours) < 9:
            return []

        # Step 2/4: Find the contour that has 9 neighbors (including itself)
        # and return all of those neighbors.
        found = False
        contour_neighbors = {}
        for index, contour in enumerate(final_contours):
            (x, y, w, h) = contour
            contour_neighbors[index] = []
            center_x = x + w / 2
            center_y = y + h / 2
            radius = 1.5

            # Create 9 positions for the current contour which are the
            # neighbors. We'll use this to check how many neighbors each contour
            # has. The only way all of these can match is if the current contour
            # is the center of the cube. If we found the center, we also know
            # all the neighbors, thus knowing all the contours and thus knowing
            # this shape can be considered a 3x3x3 cube. When we've found those
            # contours, we sort them and return them.
            neighbor_positions = [
                # top left
                [(center_x - w * radius), (center_y - h * radius)],

                # top middle
                [center_x, (center_y - h * radius)],

                # top right
                [(center_x + w * radius), (center_y - h * radius)],

                # middle left
                [(center_x - w * radius), center_y],

                # center
                [center_x, center_y],

                # middle right
                [(center_x + w * radius), center_y],

                # bottom left
                [(center_x - w * radius), (center_y + h * radius)],

                # bottom middle
                [center_x, (center_y + h * radius)],

                # bottom right
                [(center_x + w * radius), (center_y + h * radius)],
            ]

            for neighbor in final_contours:
                (x2, y2, w2, h2) = neighbor
                for (x3, y3) in neighbor_positions:
                    # The neighbor_positions are located in the center of each
                    # contour instead of top-left corner.
                    # logic: (top left < center pos) and (bottom right > center pos)
                    if (x2 < x3 and y2 < y3) and (x2 + w2 > x3 and y2 + h2 > y3):
                        contour_neighbors[index].append(neighbor)

        # Step 3/4: Now that we know how many neighbors all contours have, we'll
        # loop over them and find the contour that has 9 neighbors, which
        # includes itself. This is the center piece of the cube. If we come
        # across it, then the 'neighbors' are actually all the contours we're
        # looking for.
        for (contour, neighbors) in contour_neighbors.items():
            if len(neighbors) == 9:
                found = True
                final_contours = neighbors
                break

        if not found:
            return []

        # Step 4/4: When we reached this part of the code we found a cube-like
        # contour. The code below will sort all the contours on their X and Y
        # values from the top-left to the bottom-right.

        # Sort contours on the y-value first.
        y_sorted = sorted(final_contours, key=lambda item: item[1])

        # Split into 3 rows and sort each row on the x-value.
        top_row = sorted(y_sorted[0:3], key=lambda item: item[0])
        middle_row = sorted(y_sorted[3:6], key=lambda item: item[0])
        bottom_row = sorted(y_sorted[6:9], key=lambda item: item[0])

        sorted_contours = top_row + middle_row + bottom_row
        return sorted_contours

    def scanned_successfully(self):
        """Validate if the user scanned 9 colors for each side."""
        color_count = {}
        for side, preview in self.result_state.items():
            for bgr in preview:
                key = str(bgr)
                if not key in color_count:
                    color_count[key] = 1
                else:
                    color_count[key] = color_count[key] + 1
        invalid_colors = [k for k, v in color_count.items() if v != 9]
        return len(invalid_colors) == 0

    def draw_contours(self, frame, contours):
        """Draw contours onto the given frame."""
        if self.calibrate_mode:
            # Only show the center piece contour.
            (x, y, w, h) = contours[4]
            cv2.rectangle(frame, (x, y), (x + w, y + h), STICKER_CONTOUR_COLOR, 2)
        else:
            for index, (x, y, w, h) in enumerate(contours):
                cv2.rectangle(frame, (x, y), (x + w, y + h), STICKER_CONTOUR_COLOR, 2)

    def update_preview_state(self, frame, contours):
        """
        Get the average color value for the contour for every X amount of frames
        to prevent flickering and more precise results.
        """
        max_average_rounds = 8
        for index, (x, y, w, h) in enumerate(contours):
            if index in self.average_sticker_colors and len(self.average_sticker_colors[index]) == max_average_rounds:
                sorted_items = {}
                for bgr in self.average_sticker_colors[index]:
                    key = str(bgr)
                    if key in sorted_items:
                        sorted_items[key] += 1
                    else:
                        sorted_items[key] = 1
                most_common_color = max(sorted_items, key=lambda i: sorted_items[i])
                self.average_sticker_colors[index] = []
                self.preview_state[index] = eval(most_common_color)
                break

            roi = frame[y+7:y+h-7, x+14:x+w-14]
            avg_bgr = color_detector.get_dominant_color(roi)
            closest_color = color_detector.get_closest_color(avg_bgr)['color_bgr']
            self.preview_state[index] = closest_color
            if index in self.average_sticker_colors:
                self.average_sticker_colors[index].append(closest_color)
            else:
                self.average_sticker_colors[index] = [closest_color]

    def update_snapshot_state(self, frame):
        """Update the snapshot state based on the current preview state."""
        self.snapshot_state = list(self.preview_state)
        center_color_name = color_detector.get_closest_color(self.snapshot_state[4])['color_name']
        self.result_state[center_color_name] = self.snapshot_state
        self.draw_snapshot_stickers(frame)

    def auto_update_snapshot_state(self, frame):
        """Update the snapshot state based on the current preview state."""
        self.snapshot_state = list(self.preview_state)
        center_color_name = color_detector.get_closest_color(self.snapshot_state[4])['color_name']
        if center_color_name not in self.result_state:
                self.result_state[center_color_name] = self.snapshot_state
                self.draw_snapshot_stickers(frame)
                #self.calib_next = True

    def get_freetype2_font(self):
        """Get the freetype2 font, load it and return it."""
        font_path = '{}/assets/arial-unicode-ms.ttf'.format(ROOT_DIR)
        ft2 = cv2.freetype.createFreeType2()
        ft2.loadFontData(font_path, 0)
        return ft2

    def render_text(self, frame, text, pos, color=(0, 0, 0), fontScale=1.0, thickness=1, bottomLeftOrigin=False):
        """Render text with a shadow."""
        # ft2 = self.get_freetype2_font()
        # self.get_text_size(text)
        # ft2.putText(frame, text, pos, fontHeight=size, color=(0, 0, 0), thickness=2, line_type=cv2.LINE_AA, bottomLeftOrigin=bottomLeftOrigin)
        # ft2.putText(frame, text, pos, fontHeight=size, color=color, thickness=-1, line_type=cv2.LINE_AA, bottomLeftOrigin=bottomLeftOrigin)

        font                   = cv2.FONT_HERSHEY_COMPLEX_SMALL 


        #cv2.putText(frame, text,     bottomLeftCornerOfText,     font,     size,    color,    thickness,    cv2.LINE_AA)
        cv2.putText(frame, text, pos, font, fontScale, color, thickness, cv2.LINE_AA)

    def get_text_size(self, text, size=TEXT_SIZE):
        """Get text size based on the default freetype2 loaded font."""
        ft2 = self.get_freetype2_font()
        return ft2.getTextSize(text, size, thickness=-1)

    def draw_scanned_sides(self, frame):
        """Display how many sides are scanned by the user."""
        text = i18n.t('scannedSides', num=len(self.result_state.keys()))
        self.render_text(frame, text, (20, self.height - 20), bottomLeftOrigin=True)

    def draw_current_color_to_calibrate(self, frame):
        """Display the current side's color that needs to be calibrated."""
        y_offset = 20
        font_size = int(TEXT_SIZE * 1.25)
        if self.done_calibrating:
            messages = [
                i18n.t('calibratedSuccessfully'),
                i18n.t('quitCalibrateMode', keyValue=CALIBRATE_MODE_KEY),
            ]
            for index, text in enumerate(messages):
                font_size
                #(textsize_width, textsize_height), _ = self.get_text_size(text, font_size)
                y = y_offset + (8 + 10) * index
                self.render_text(frame, text, (int(self.width / 2 - 8 / 2), y), fontScale=1)
        else:
            current_color = self.colors_to_calibrate[self.current_color_to_calibrate_index]
            text = i18n.t('currentCalibratingSide.{}'.format(current_color))
            #(textsize_width, textsize_height), _ = self.get_text_size(text, font_size)
            self.render_text(frame, text, (int(self.width / 2 - 8 / 2), y_offset), fontScale=1)

    def draw_calibrated_colors(self, frame):
        """Display all the colors that are calibrated while in calibrate mode."""
        offset_y = 20
        for index, (color_name, color_bgr) in enumerate(self.calibrated_colors.items()):
            x1 = 90
            y1 = int(offset_y + STICKER_AREA_TILE_SIZE * index)
            x2 = x1 + STICKER_AREA_TILE_SIZE
            y2 = y1 + STICKER_AREA_TILE_SIZE

            # shadow
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 0, 0),
                -1
            )

            # foreground
            cv2.rectangle(
                frame,
                (x1 + 1, y1 + 1),
                (x2 - 1, y2 - 1),
                tuple([int(c) for c in color_bgr]),
                -1
            )
            self.render_text(frame, i18n.t(color_name), (10, y1 + (y2-y1)//2))

    def reset_calibrate_mode(self):
        """Reset calibrate mode variables."""
        self.calibrated_colors = {}
        self.current_color_to_calibrate_index = 0
        self.done_calibrating = False

    def draw_current_language(self, frame):
        # text = '{}: {}'.format(
        #     i18n.t('language'),
        #     LOCALES[config.get_setting('locale')]
        # )
        # #(textsize_width, textsize_height), _ = self.get_text_size(text)
        # offset = 20
        # self.render_text(frame, text, (self.width - 150 - offset, offset))
        return

    def draw_keys(self, frame):
        self.render_text(frame, 'capture side: <SPACE>', (self.width - 170, 15), fontScale=0.6)
        self.render_text(frame, '(c)alibrate', (self.width - 100, 30), fontScale=0.6)
        self.render_text(frame, '(s)olve',     (self.width - 100, 45), fontScale=0.6)
        self.render_text(frame, '(r)eset',     (self.width - 100, 60), fontScale=0.6)

    def draw_2d_cube_state(self, frame):
        """
        Create a 2D cube state visualization and draw the self.result_state.

        We're gonna display the visualization like so:
                    -----
                  | W W W |
                  | W W W |
                  | W W W |
            -----   -----   -----   -----
          | O O O | G G G | R R R | B B B |
          | O O O | G G G | R R R | B B B |
          | O O O | G G G | R R R | B B B |
            -----   -----   -----   -----
                  | Y Y Y |
                  | Y Y Y |
                  | Y Y Y |
                    -----
        So we're gonna make a 4x3 grid and hardcode where each side has to go.
        Based on the x and y in that 4x3 grid we can calculate its position.
        """
        grid = {
            'white' : [1, 0],
            'orange': [0, 1],
            'green' : [1, 1],
            'red'   : [2, 1],
            'blue'  : [3, 1],
            'yellow': [1, 2],
        }

        # The offset in-between each side (white, red, etc).
        side_offset = MINI_STICKER_AREA_TILE_GAP * 3

        # The size of 1 whole side (containing 9 stickers).
        side_size = MINI_STICKER_AREA_TILE_SIZE * 3 + MINI_STICKER_AREA_TILE_GAP * 2

        # The X and Y offset is placed in the bottom-right corner, minus the
        # whole size of the 4x3 grid, minus an additional offset.
        offset_x = self.width - (side_size * 4) - (side_offset * 3) - MINI_STICKER_AREA_OFFSET
        offset_y = self.height - (side_size * 3) - (side_offset * 2) - MINI_STICKER_AREA_OFFSET

        for side, (grid_x, grid_y) in grid.items():
            index = -1
            for row in range(3):
                for col in range(3):
                    index += 1
                    x1 = int((offset_x + MINI_STICKER_AREA_TILE_SIZE * col) + (MINI_STICKER_AREA_TILE_GAP * col) + ((side_size + side_offset) * grid_x))
                    y1 = int((offset_y + MINI_STICKER_AREA_TILE_SIZE * row) + (MINI_STICKER_AREA_TILE_GAP * row) + ((side_size + side_offset) * grid_y))
                    x2 = int(x1 + MINI_STICKER_AREA_TILE_SIZE)
                    y2 = int(y1 + MINI_STICKER_AREA_TILE_SIZE)

                    foreground_color = COLOR_PLACEHOLDER
                    if side in self.result_state:
                        foreground_color = color_detector.get_prominent_color(self.result_state[side][index])

                    # shadow
                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 0, 0),
                        -1
                    )

                    # foreground color
                    cv2.rectangle(
                        frame,
                        (x1 + 1, y1 + 1),
                        (x2 - 1, y2 - 1),
                        foreground_color,
                        -1
                    )

    def get_result_notation(self):
        """Convert all the sides and their BGR colors to cube notation."""
        notation = dict(self.result_state)
        for side, preview in notation.items():
            for sticker_index, bgr in enumerate(preview):
                notation[side][sticker_index] = color_detector.convert_bgr_to_notation(bgr)

        # Join all the sides together into one single string.
        # Order must be URFDLB (white, red, green, yellow, orange, blue)
        combined = ''
        for side in ['white', 'red', 'green', 'yellow', 'orange', 'blue']:
            combined += ''.join(notation[side])
        return combined

    def state_already_solved(self):
        """Find out if the cube hasn't been solved already."""
        if len(self.result_state.keys()) != 6:
            return False

        for side in ['white', 'red', 'green', 'yellow', 'orange', 'blue']:
            # Get the center color of the current side.
            center_bgr = self.result_state[side][4]

            # Compare the center color to all neighbors. If we come across a
            # different color, then we can assume the cube isn't solved yet.
            for bgr in self.result_state[side]:
                if center_bgr != bgr:
                    return False
        return True

    def start_solve(self):
        if len(self.result_state.keys()) != 6:
            print('\033[0;33m[{}] {}'.format(i18n.t('error'), i18n.t('haventScannedAllSides')))
            return

        if not self.scanned_successfully():
            print('\033[0;33m[{}] {}'.format(i18n.t('error'), i18n.t('haventScannedAllSides')))
            return

        if self.state_already_solved():
            print('\033[0;33m[{}] {}'.format(i18n.t('error'), i18n.t('cubeAlreadySolved')))
            return

        else:
            note = self.get_result_notation()
            self.qbr.solve_cube(note)
            return

    def run(self):
        """
        Open up the webcam and present the user with the Qbr user interface.

        Returns a string of the scanned state in rubik's cube notation.
        """
        while True:
            ret, frame = self.cam.read()
            if not ret:
               continue
            grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurredFrame = cv2.blur(grayFrame, (3, 3))
            cannyFrame = cv2.Canny(blurredFrame, 30, 60, 3)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilatedFrame = cv2.dilate(cannyFrame, kernel)

            contours = self.find_contours(dilatedFrame)
            if len(contours) == 9:
                self.draw_contours(frame, contours)
                if not self.calibrate_mode:
                    self.update_preview_state(frame, contours)
                elif key == 32 and self.done_calibrating == False:
                    current_color = self.colors_to_calibrate[self.current_color_to_calibrate_index]
                    (x, y, w, h) = contours[4]
                    roi = frame[y+7:y+h-7, x+14:x+w-14]
                    avg_bgr = color_detector.get_dominant_color(roi)
                    self.calibrated_colors[current_color] = avg_bgr
                    self.current_color_to_calibrate_index += 1
                    self.done_calibrating = self.current_color_to_calibrate_index == len(self.colors_to_calibrate)
                    if self.done_calibrating:
                        color_detector.set_cube_color_pallete(self.calibrated_colors)
                        config.set_setting(CUBE_PALETTE, color_detector.cube_color_palette)

            if self.calibrate_mode:
                self.draw_current_color_to_calibrate(frame)
                self.draw_calibrated_colors(frame)
            else:
                self.draw_keys(frame)
                self.draw_preview_stickers(frame)
                self.draw_snapshot_stickers(frame)
                self.draw_scanned_sides(frame)
                self.draw_2d_cube_state(frame)

            cv2.imshow("Qbr - Rubik's cube solver", frame)

            key = cv2.waitKey(10) & 0xff

            # Quit on escape.
            if key == 27:
                break

            if key == ord(SOLVE_CUBE_KEY):
                
                #self.qbr.send_to_remote_serial("U B")
                if not self.calibrate_mode:
                    config.set_setting(CUBE_SAVED_STATE, self.result_state)
                    self.start_solve()
                    self.reset()

            if not self.calibrate_mode:
                # Update the snapshot when space bar is pressed.
                if key == 32:
                    self.update_snapshot_state(frame)
                
                if(self.qbr.autoscan):
                    self.auto_update_snapshot_state(frame)

                # Switch to another language.
                # if key == ord(SWITCH_LANGUAGE_KEY):
                #     next_locale = get_next_locale(config.get_setting('locale'))
                #     config.set_setting('locale', next_locale)
                #     i18n.set('locale', next_locale)

            # Toggle calibrate mode.
            if key == ord(CALIBRATE_MODE_KEY):
                self.reset_calibrate_mode()
                self.calibrate_mode = not self.calibrate_mode

            if key == ord(RESET_CUBE_KEY):
                self.reset()             

            # Exit on window close
            if cv2.getWindowProperty("Qbr - Rubik's cube solver", 0) == -1:
                break


        self.cam.release()
        cv2.destroyAllWindows()
