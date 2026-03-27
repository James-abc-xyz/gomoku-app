"""
五子棋 Android App
框架: Kivy
功能: 人机对战 / 双人对战
AI: Minimax + Alpha-Beta 剪枝
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from kivy.utils import platform
import math
import copy
import threading

# 棋盘大小
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1  # 玩家
WHITE = 2  # AI

# AI 搜索深度
AI_DEPTH = 3

# 分值表
SCORE_TABLE = {
    (1, 0): 10,
    (2, 0): 100,
    (3, 0): 1000,
    (4, 0): 10000,
    (5, 0): 1000000,
    (1, 1): 5,
    (2, 1): 50,
    (3, 1): 500,
    (4, 1): 5000,
}


def check_win(board, player):
    """检查玩家是否获胜"""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                for dr, dc in directions:
                    count = 1
                    for i in range(1, 5):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                            count += 1
                        else:
                            break
                    if count >= 5:
                        return True
    return False


def get_winning_cells(board, player):
    """获取获胜的五个棋子坐标"""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                for dr, dc in directions:
                    cells = [(r, c)]
                    for i in range(1, 5):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                            cells.append((nr, nc))
                        else:
                            break
                    if len(cells) >= 5:
                        return cells[:5]
    return []


def evaluate_line(line, player):
    """评估一条线的分数"""
    opponent = WHITE if player == BLACK else BLACK
    score = 0
    n = len(line)
    i = 0
    while i < n:
        if line[i] == player:
            count = 0
            open_ends = 0
            if i == 0 or line[i - 1] == EMPTY:
                open_ends += 1
            j = i
            while j < n and line[j] == player:
                count += 1
                j += 1
            if j == n or line[j] == EMPTY:
                open_ends += 1
            if count >= 5:
                score += 1000000
            elif count in (1, 2, 3, 4):
                blocked = 2 - open_ends
                score += SCORE_TABLE.get((count, blocked), 0)
            i = j
        else:
            i += 1
    return score


def evaluate_board(board, player):
    """评估整个棋盘的分数"""
    score = 0
    opponent = WHITE if player == BLACK else BLACK
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for dr, dc in directions:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if dr == 1 and dc == 0:
                    line = [board[r + i][c] for i in range(BOARD_SIZE - r) if 0 <= r + i < BOARD_SIZE]
                    if len(line) < 5:
                        continue
                    score += evaluate_line(line, player)
                    score -= evaluate_line(line, opponent) * 1.2
                elif dr == 0 and dc == 1:
                    line = [board[r][c + i] for i in range(BOARD_SIZE - c) if 0 <= c + i < BOARD_SIZE]
                    if len(line) < 5:
                        continue
                    score += evaluate_line(line, player)
                    score -= evaluate_line(line, opponent) * 1.2
                elif dr == 1 and dc == 1:
                    line = []
                    nr, nc = r, c
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        line.append(board[nr][nc])
                        nr += 1
                        nc += 1
                    if len(line) < 5:
                        continue
                    score += evaluate_line(line, player)
                    score -= evaluate_line(line, opponent) * 1.2
                elif dr == 1 and dc == -1:
                    line = []
                    nr, nc = r, c
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        line.append(board[nr][nc])
                        nr += 1
                        nc -= 1
                    if len(line) < 5:
                        continue
                    score += evaluate_line(line, player)
                    score -= evaluate_line(line, opponent) * 1.2
    return score


def get_candidates(board, player):
    """获取候选落子位置（已有棋子周围2格内的空位）"""
    candidates = set()
    has_piece = False
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                has_piece = True
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            candidates.add((nr, nc))
    if not has_piece:
        candidates.add((BOARD_SIZE // 2, BOARD_SIZE // 2))
    return list(candidates)


def minimax(board, depth, alpha, beta, maximizing, ai_player):
    """Minimax + Alpha-Beta 剪枝"""
    human = BLACK if ai_player == WHITE else WHITE

    if check_win(board, ai_player):
        return 1000000 + depth, None
    if check_win(board, human):
        return -1000000 - depth, None

    candidates = get_candidates(board, ai_player)
    if depth == 0 or not candidates:
        return evaluate_board(board, ai_player), None

    best_move = None

    if maximizing:
        max_score = -math.inf
        for r, c in candidates:
            board[r][c] = ai_player
            score, _ = minimax(board, depth - 1, alpha, beta, False, ai_player)
            board[r][c] = EMPTY
            if score > max_score:
                max_score = score
                best_move = (r, c)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score, best_move
    else:
        min_score = math.inf
        for r, c in candidates:
            board[r][c] = human
            score, _ = minimax(board, depth - 1, alpha, beta, True, ai_player)
            board[r][c] = EMPTY
            if score < min_score:
                min_score = score
                best_move = (r, c)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score, best_move


def ai_move(board):
    """AI计算最佳落子"""
    _, move = minimax(board, AI_DEPTH, -math.inf, math.inf, True, WHITE)
    if move is None:
        candidates = get_candidates(board, WHITE)
        if candidates:
            move = candidates[0]
    return move


# ======================== UI 部分 ========================

class GomokuBoard(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.bind(size=self._update_canvas, pos=self._update_canvas)

    def _update_canvas(self, *args):
        self.draw()

    def get_cell_size(self):
        return min(self.width, self.height) / (BOARD_SIZE + 1)

    def get_board_origin(self):
        cell = self.get_cell_size()
        ox = self.x + (self.width - cell * (BOARD_SIZE - 1)) / 2
        oy = self.y + (self.height - cell * (BOARD_SIZE - 1)) / 2
        return ox, oy

    def rc_to_xy(self, row, col):
        cell = self.get_cell_size()
        ox, oy = self.get_board_origin()
        x = ox + col * cell
        y = oy + (BOARD_SIZE - 1 - row) * cell
        return x, y

    def xy_to_rc(self, x, y):
        cell = self.get_cell_size()
        ox, oy = self.get_board_origin()
        col = round((x - ox) / cell)
        row = round((BOARD_SIZE - 1) - (y - oy) / cell)
        return row, col

    def draw(self):
        self.canvas.clear()
        cell = self.get_cell_size()
        ox, oy = self.get_board_origin()

        with self.canvas:
            # 棋盘背景
            Color(0.85, 0.65, 0.2, 1)
            Rectangle(pos=(self.x, self.y), size=(self.width, self.height))

            # 网格线
            Color(0.1, 0.1, 0.1, 1)
            for i in range(BOARD_SIZE):
                # 横线
                Line(points=[ox, oy + i * cell, ox + (BOARD_SIZE - 1) * cell, oy + i * cell], width=1)
                # 竖线
                Line(points=[ox + i * cell, oy, ox + i * cell, oy + (BOARD_SIZE - 1) * cell], width=1)

            # 星位（天元和4个星）
            star_points = [
                (7, 7),  # 天元
                (3, 3), (3, 11), (11, 3), (11, 11),
            ]
            Color(0.1, 0.1, 0.1, 1)
            for sr, sc in star_points:
                sx, sy = self.rc_to_xy(sr, sc)
                r = cell * 0.12
                Ellipse(pos=(sx - r, sy - r), size=(r * 2, r * 2))

            # 绘制棋子
            board = self.game.board
            winning = self.game.winning_cells
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if board[row][col] != EMPTY:
                        cx, cy = self.rc_to_xy(row, col)
                        radius = cell * 0.45
                        is_winning = (row, col) in winning

                        if board[row][col] == BLACK:
                            # 黑棋
                            Color(0.05, 0.05, 0.05, 1)
                            Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))
                            if is_winning:
                                Color(1, 0, 0, 0.8)
                                Line(circle=(cx, cy, radius * 0.7), width=2.5)
                        else:
                            # 白棋
                            Color(0.95, 0.95, 0.95, 1)
                            Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))
                            Color(0.6, 0.6, 0.6, 1)
                            Line(circle=(cx, cy, radius), width=1.2)
                            if is_winning:
                                Color(1, 0, 0, 0.8)
                                Line(circle=(cx, cy, radius * 0.7), width=2.5)

            # 最后落子标记
            if self.game.last_move:
                lr, lc = self.game.last_move
                lx, ly = self.rc_to_xy(lr, lc)
                r = cell * 0.15
                Color(1, 0.3, 0.3, 1)
                Ellipse(pos=(lx - r, ly - r), size=(r * 2, r * 2))

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        self.game.on_board_touch(touch.x, touch.y)
        return True


class GomokuGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 0

        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.game_over = False
        self.ai_thinking = False
        self.vs_ai = True  # True=人机，False=双人
        self.last_move = None
        self.winning_cells = []
        self.black_count = 0
        self.white_count = 0

        self._build_ui()

    def _build_ui(self):
        # 顶部状态栏
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        top_bar.padding = [10, 5]
        top_bar.spacing = 10

        with top_bar.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self._top_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(pos=lambda *a: setattr(self._top_rect, 'pos', top_bar.pos),
                     size=lambda *a: setattr(self._top_rect, 'size', top_bar.size))

        self.status_label = Label(
            text='你的回合（黑棋）',
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True,
            size_hint=(1, 1),
            halign='center'
        )
        top_bar.add_widget(self.status_label)
        self.add_widget(top_bar)

        # 模式切换栏
        mode_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=44)
        mode_bar.padding = [8, 4]
        mode_bar.spacing = 8

        with mode_bar.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self._mode_rect = Rectangle(pos=mode_bar.pos, size=mode_bar.size)
        mode_bar.bind(pos=lambda *a: setattr(self._mode_rect, 'pos', mode_bar.pos),
                      size=lambda *a: setattr(self._mode_rect, 'size', mode_bar.size))

        self.btn_vs_ai = Button(
            text='人机对战',
            font_size='14sp',
            background_color=(0.2, 0.6, 0.9, 1),
            size_hint=(1, 1)
        )
        self.btn_vs_human = Button(
            text='双人对战',
            font_size='14sp',
            background_color=(0.3, 0.3, 0.3, 1),
            size_hint=(1, 1)
        )
        self.btn_vs_ai.bind(on_press=lambda x: self.set_mode(True))
        self.btn_vs_human.bind(on_press=lambda x: self.set_mode(False))
        mode_bar.add_widget(self.btn_vs_ai)
        mode_bar.add_widget(self.btn_vs_human)
        self.add_widget(mode_bar)

        # 棋盘区域
        self.board_widget = GomokuBoard(game=self, size_hint=(1, 1))
        self.add_widget(self.board_widget)

        # 底部按钮
        btn_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=54)
        btn_bar.padding = [10, 6]
        btn_bar.spacing = 10

        with btn_bar.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self._btn_rect = Rectangle(pos=btn_bar.pos, size=btn_bar.size)
        btn_bar.bind(pos=lambda *a: setattr(self._btn_rect, 'pos', btn_bar.pos),
                     size=lambda *a: setattr(self._btn_rect, 'size', btn_bar.size))

        btn_restart = Button(
            text='重新开始',
            font_size='15sp',
            background_color=(0.8, 0.3, 0.3, 1),
            size_hint=(1, 1)
        )
        btn_undo = Button(
            text='悔棋',
            font_size='15sp',
            background_color=(0.3, 0.6, 0.3, 1),
            size_hint=(0.7, 1)
        )
        btn_restart.bind(on_press=lambda x: self.restart())
        btn_undo.bind(on_press=lambda x: self.undo())
        btn_bar.add_widget(btn_restart)
        btn_bar.add_widget(btn_undo)
        self.add_widget(btn_bar)

        self._history = []

    def set_mode(self, vs_ai):
        self.vs_ai = vs_ai
        if vs_ai:
            self.btn_vs_ai.background_color = (0.2, 0.6, 0.9, 1)
            self.btn_vs_human.background_color = (0.3, 0.3, 0.3, 1)
        else:
            self.btn_vs_ai.background_color = (0.3, 0.3, 0.3, 1)
            self.btn_vs_human.background_color = (0.2, 0.8, 0.5, 1)
        self.restart()

    def restart(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.game_over = False
        self.ai_thinking = False
        self.last_move = None
        self.winning_cells = []
        self._history = []
        self._update_status()
        self.board_widget.draw()

    def undo(self):
        if self.game_over or self.ai_thinking:
            return
        if self.vs_ai:
            # 人机模式撤销2步
            if len(self._history) >= 2:
                r, c = self._history.pop()
                self.board[r][c] = EMPTY
                r, c = self._history.pop()
                self.board[r][c] = EMPTY
                self.last_move = self._history[-1] if self._history else None
                self.current_player = BLACK
                self._update_status()
                self.board_widget.draw()
        else:
            if self._history:
                r, c = self._history.pop()
                self.board[r][c] = EMPTY
                self.last_move = self._history[-1] if self._history else None
                self.current_player = BLACK if self.current_player == WHITE else WHITE
                self._update_status()
                self.board_widget.draw()

    def _update_status(self):
        if self.game_over:
            return
        if self.vs_ai:
            if self.current_player == BLACK:
                self.status_label.text = '你的回合（黑棋）'
                self.status_label.color = (0.4, 1, 0.4, 1)
            else:
                self.status_label.text = 'AI 思考中...'
                self.status_label.color = (1, 0.8, 0.3, 1)
        else:
            if self.current_player == BLACK:
                self.status_label.text = '黑棋落子'
                self.status_label.color = (0.4, 1, 0.4, 1)
            else:
                self.status_label.text = '白棋落子'
                self.status_label.color = (1, 1, 1, 1)

    def on_board_touch(self, x, y):
        if self.game_over or self.ai_thinking:
            return
        if self.vs_ai and self.current_player == WHITE:
            return

        row, col = self.board_widget.xy_to_rc(x, y)
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        if self.board[row][col] != EMPTY:
            return

        self._place(row, col, self.current_player)

        if self.vs_ai and not self.game_over:
            self.current_player = WHITE
            self._update_status()
            self.board_widget.draw()
            self.ai_thinking = True
            t = threading.Thread(target=self._ai_thread)
            t.daemon = True
            t.start()

    def _place(self, row, col, player):
        self.board[row][col] = player
        self.last_move = (row, col)
        self._history.append((row, col))

        if check_win(self.board, player):
            self.winning_cells = get_winning_cells(self.board, player)
            self.game_over = True
            self.board_widget.draw()
            self._show_result(player)
            return

        # 检查平局
        if all(self.board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)):
            self.game_over = True
            self.board_widget.draw()
            self._show_result(None)
            return

        if not self.vs_ai:
            self.current_player = WHITE if player == BLACK else BLACK
            self._update_status()
            self.board_widget.draw()

    def _ai_thread(self):
        move = ai_move(self.board)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._ai_done(move))

    def _ai_done(self, move):
        self.ai_thinking = False
        if move and not self.game_over:
            self._place(move[0], move[1], WHITE)
            if not self.game_over:
                self.current_player = BLACK
                self._update_status()
                self.board_widget.draw()

    def _show_result(self, winner):
        if winner == BLACK:
            if self.vs_ai:
                title = '🎉 你赢了！'
                msg = '恭喜！你击败了AI！'
            else:
                title = '🎉 黑棋获胜！'
                msg = '黑棋五子连珠，胜利！'
            self.status_label.text = title
            self.status_label.color = (1, 0.5, 0, 1)
        elif winner == WHITE:
            if self.vs_ai:
                title = '😞 AI 获胜'
                msg = 'AI五子连珠，再接再厉！'
            else:
                title = '🎉 白棋获胜！'
                msg = '白棋五子连珠，胜利！'
            self.status_label.text = title
            self.status_label.color = (0.8, 0.8, 1, 1)
        else:
            title = '平局'
            msg = '棋盘已满，平局！'
            self.status_label.text = '平局'
            self.status_label.color = (1, 1, 0.3, 1)

        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(text=msg, font_size='18sp', color=(0.1, 0.1, 0.1, 1)))

        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=48, spacing=10)
        btn_restart = Button(text='再来一局', font_size='16sp', background_color=(0.2, 0.6, 0.9, 1))
        btn_close = Button(text='继续查看', font_size='16sp', background_color=(0.5, 0.5, 0.5, 1))

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.35),
            title_color=(0.1, 0.1, 0.1, 1),
            background='',
            separator_color=(0.3, 0.3, 0.3, 1),
        )

        btn_restart.bind(on_press=lambda x: [popup.dismiss(), self.restart()])
        btn_close.bind(on_press=popup.dismiss)
        btn_layout.add_widget(btn_restart)
        btn_layout.add_widget(btn_close)
        content.add_widget(btn_layout)

        popup.open()


class GomokuApp(App):
    def build(self):
        self.title = '五子棋'
        if platform == 'android':
            Window.fullscreen = 'auto'
        else:
            Window.size = (400, 700)
        game = GomokuGame()
        return game


if __name__ == '__main__':
    GomokuApp().run()
