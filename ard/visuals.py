import pygame
import numpy as np
import time
from dataclasses import dataclass

@dataclass
class Domino:
    x: int
    y: int
    orientation: str  # 'U', 'D', 'L', or 'R'

class ArcticCircleSimulator:

    def __init__(self, size=16, cell_size=40, display_size=(1920, 1080)):
        """
        Initialize the Arctic Circle Theorem domino tiling simulator.

        Args:
            size: Size of the Aztec diamond (must be even)
            cell_size: Size of each cell in pixels
            display_size: Size of the display window
        """
        # Ensure size is even
        self.size = max(4, size if size % 2 == 0 else size + 1)
        self.cell_size = cell_size
        self.display_size = display_size

        # Initialize PyGame
        pygame.init()
        # Use DOUBLEBUF flag to reduce flickering
        self.screen = pygame.display.set_mode(display_size,
                                              pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE)
        pygame.display.set_caption("Arctic Circle Theorem - Domino Tiling Simulator")
        self.clock = pygame.time.Clock()

        # Create board and dominos
        self.init_board()

        # Colors for dominos (red, green, blue, yellow)
        self.colors = [
            (220, 60, 60),  # Red
            (60, 180, 60),  # Green
            (60, 60, 220),  # Blue
            (220, 220, 60)  # Yellow
        ]

        # Camera/view controls
        self.camera_x = self.display_size[0] // 2 - (self.size * self.cell_size) // 2
        self.camera_y = self.display_size[1] // 2 - (self.size * self.cell_size) // 2
        self.camera_zoom = 1.0

        # Input tracking
        self.panning = False
        self.pan_start_pos = None
        self.last_mouse_pos = (0, 0)

        # Create a background surface to avoid redrawing static elements
        self.bg_surface = None
        self.should_redraw_bg = True

        # Performance tracking
        self.fps = 0
        self.last_time = time.time()
        self.frame_count = 0

        # Limit framerate to reduce flickering
        self.target_fps = 60

    def init_board(self):
        """Initialize the board and dominos for an Aztec diamond of the given size."""
        # Create board as a 2D array (value = domino index or -1 for masked cells)
        self.board = np.zeros((self.size, self.size), dtype=np.int32)

        # Mask off corners to create Aztec diamond shape
        half_size = self.size // 2
        for i in range(self.size):
            for j in range(self.size):
                # Proper corner masking: N/2 - 1 on each corner
                # For an 8x8 board, mask 3+2+1 tiles on each corner
                if i + j < half_size - 1 or \
                   i + j > self.size + half_size - 2 or \
                   i - j > half_size - 1 or \
                   j - i > half_size - 1:
                    self.board[i, j] = -1

        # Create structured array for dominos
        self.dominos = []
        self.generate_random_tiling()
        self.should_redraw_bg = True

    def generate_random_tiling(self):
        """Generate a random valid tiling of the Aztec diamond."""
        # Reset board (keeping mask)
        mask = (self.board == -1)
        self.board = np.zeros_like(self.board)
        self.board[mask] = -1

        # List of valid cells (not masked)
        valid_cells = [(i, j) for i in range(self.size) for j in range(self.size) if self.board[i, j] == 0]
        np.random.shuffle(valid_cells)

        # Place dominos
        self.dominos = []
        domino_idx = 1

        while valid_cells:
            i, j = valid_cells[0]
            if self.board[i, j] != 0:  # Already covered
                valid_cells.pop(0)
                continue

            # Try to place a domino in one of 4 orientations
            orientations = ['R', 'D', 'L', 'U']
            np.random.shuffle(orientations)

            placed = False
            for orientation in orientations:
                if orientation == 'R' and j + 1 < self.size and self.board[i, j + 1] == 0:
                    self.board[i, j] = domino_idx
                    self.board[i, j + 1] = domino_idx
                    self.dominos.append(Domino(x=i, y=j, orientation='R'))
                    placed = True
                    break
                elif orientation == 'D' and i + 1 < self.size and self.board[i + 1, j] == 0:
                    self.board[i, j] = domino_idx
                    self.board[i + 1, j] = domino_idx
                    self.dominos.append(Domino(x=i, y=j, orientation='D'))
                    placed = True
                    break
                elif orientation == 'L' and j - 1 >= 0 and self.board[i, j - 1] == 0:
                    self.board[i, j] = domino_idx
                    self.board[i, j - 1] = domino_idx
                    self.dominos.append(Domino(x=i - 1 if orientation == 'L' else i, y=j - 1, orientation='R'))
                    placed = True
                    break
                elif orientation == 'U' and i - 1 >= 0 and self.board[i - 1, j] == 0:
                    self.board[i, j] = domino_idx
                    self.board[i - 1, j] = domino_idx
                    self.dominos.append(Domino(x=i - 1, y=j, orientation='D'))
                    placed = True
                    break

            if placed:
                domino_idx += 1

            valid_cells.pop(0)

        self.should_redraw_bg = True

    def resize_aztec_diamond(self, new_size):
        """Resize the Aztec diamond to a new size."""
        print(f'resize_diamond {new_size} {self.size}', flush=True)
        if new_size % 2 != 0: new_size += 1
        self.size = max(4, new_size)
        self.init_board()
        self.should_redraw_bg = True

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Right mouse button for zooming
                if event.button == 3:  # Right mouse button
                    self.last_mouse_pos = pygame.mouse.get_pos()
                # Middle mouse button for panning
                elif event.button == 2:  # Middle mouse button
                    self.panning = True
                    self.pan_start_pos = pygame.mouse.get_pos()
                # Scroll wheel for zooming
                elif event.button == 4:  # Scroll up
                    self.camera_zoom *= 1.1
                    self.should_redraw_bg = True
                elif event.button == 5:  # Scroll down
                    self.camera_zoom /= 1.1
                    self.camera_zoom = max(0.1, self.camera_zoom)
                    self.should_redraw_bg = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:  # Middle mouse button
                    self.panning = False

            elif event.type == pygame.MOUSEMOTION:
                if self.panning:
                    dx = event.pos[0] - self.pan_start_pos[0]
                    dy = event.pos[1] - self.pan_start_pos[1]
                    self.camera_x += dx
                    self.camera_y += dy
                    self.pan_start_pos = event.pos
                    self.should_redraw_bg = True

                self.last_mouse_pos = event.pos

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.resize_aztec_diamond(self.size + 2)
                    self.should_redraw_bg = True
                elif event.key == pygame.K_MINUS:
                    self.resize_aztec_diamond(self.size - 2)
                    self.should_redraw_bg = True
                elif event.key == pygame.K_SPACE:
                    self.generate_random_tiling()
                    self.should_redraw_bg = True
                elif event.key == pygame.K_ESCAPE:
                    return False

            # elif event.type == pygame.VIDEORESIZE:
            #     self.display_size = (event.w, event.h)
            #     self.screen = pygame.display.set_mode(self.display_size, #pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE)
            #     self.should_redraw_bg = True
            #
        return True

    def draw_background(self):
        """Draw the static background elements to a surface."""
        # Create a new surface if needed
        if self.bg_surface is None or self.bg_surface.get_size() != self.screen.get_size():
            self.bg_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        # Clear the surface
        self.bg_surface.fill((240, 240, 240))

        scaled_cell_size = int(self.cell_size * self.camera_zoom)

        # Only draw cells that are visible on screen (optimization)
        start_i = max(0, int((0 - self.camera_x) / scaled_cell_size))
        start_j = max(0, int((0 - self.camera_y) / scaled_cell_size))
        end_i = min(self.size, int((self.display_size[0] - self.camera_x) / scaled_cell_size) + 1)
        end_j = min(self.size, int((self.display_size[1] - self.camera_y) / scaled_cell_size) + 1)

        # Draw grid lines
        for i in range(start_i, end_i + 1):
            pygame.draw.line(
                self.bg_surface, (100, 100, 100), (self.camera_x, self.camera_y + i*scaled_cell_size),
                (self.camera_x + self.size * scaled_cell_size, self.camera_y + i*scaled_cell_size), 1)

        for j in range(start_j, end_j + 1):
            pygame.draw.line(
                self.bg_surface, (100, 100, 100), (self.camera_x + j*scaled_cell_size, self.camera_y),
                  (self.camera_x + j*scaled_cell_size, self.camera_y + self.size * scaled_cell_size), 1)

    def draw(self):
        """Draw the current state of the simulation."""
        # Redraw background if needed
        if self.should_redraw_bg:
            self.draw_background()
            self.should_redraw_bg = False

        # Blit the background to the screen
        self.screen.blit(self.bg_surface, (0, 0))

        scaled_cell_size = int(self.cell_size * self.camera_zoom)

        # Only draw cells that are visible on screen (optimization)
        start_i = max(0, int((0 - self.camera_x) / scaled_cell_size))
        start_j = max(0, int((0 - self.camera_y) / scaled_cell_size))
        end_i = min(self.size, int((self.display_size[0] - self.camera_x) / scaled_cell_size) + 1)
        end_j = min(self.size, int((self.display_size[1] - self.camera_y) / scaled_cell_size) + 1)

        # Draw each domino
        for i, domino in enumerate(self.dominos):
            x, y = domino.x, domino.y
            orientation = domino.orientation

            # Skip if outside visible area
            if (x < start_i - 1 or x >= end_i + 1 or y < start_j - 1 or y >= end_j + 1):
                continue

            color_idx = i % len(self.colors)
            color = self.colors[color_idx]

            # Determine the two cells covered by this domino
            # All dominos should be horizontal (L/R) or vertical (U/D)
            if orientation == 'R':  # horizontal domino
                rect = pygame.Rect(self.camera_x + y*scaled_cell_size, self.camera_y + x*scaled_cell_size,
                                   scaled_cell_size * 2, scaled_cell_size)
            elif orientation == 'D':  # vertical domino
                rect = pygame.Rect(self.camera_x + y*scaled_cell_size, self.camera_y + x*scaled_cell_size,
                                   scaled_cell_size, scaled_cell_size * 2)
            elif orientation == 'L':  # horizontal domino (left)
                rect = pygame.Rect(self.camera_x + (y-1) * scaled_cell_size,
                                   self.camera_y + x*scaled_cell_size, scaled_cell_size * 2, scaled_cell_size)
            elif orientation == 'U':  # vertical domino (up)
                rect = pygame.Rect(self.camera_x + y*scaled_cell_size,
                                   self.camera_y + (x-1) * scaled_cell_size, scaled_cell_size,
                                   scaled_cell_size * 2)

            # Draw domino
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

            # Draw orientation indicator
            mid_x = rect.centerx
            mid_y = rect.centery
            font_size = max(10, int(12 * self.camera_zoom))
            font = pygame.font.SysFont('Arial', font_size)
            text = font.render(orientation, True, (0, 0, 0))
            text_rect = text.get_rect(center=(mid_x, mid_y))
            self.screen.blit(text, text_rect)

        # Draw FPS counter and instructions (dynamic elements)
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time > 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time

        font = pygame.font.SysFont('Arial', 16)
        fps_text = font.render(f"FPS: {int(self.fps)}", True, (0, 0, 0))
        self.screen.blit(fps_text, (10, 10))

        # Draw instructions
        instructions = [
            "R: Generate new random tiling", "+/-: Increase/decrease diamond size",
            "Space: Generate random tiling", "Middle Mouse: Pan", "Scroll Wheel: Zoom",
            f"Size: {self.size}x{self.size}", f"Dominos: {len(self.dominos)}"
        ]

        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, (0, 0, 0))
            self.screen.blit(text, (10, 30 + i*20))

        # Update display
        pygame.display.flip()

    def run(self):
        """Run the main simulation loop."""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            # Limit the frame rate to reduce flickering
            self.clock.tick(self.target_fps)

        pygame.quit()
