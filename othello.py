#!/usr/bin/env python
"""
othello.py Humberto Henrique Campos Pinheiro
KHỞI TẠO TRÒ CHƠI VÀ VÒNG LẶP CHÍNH
- File này là điểm khởi đầu của toàn bộ game Othello
- Quản lý luồng chính: menu -> thiết lập -> chơi game -> kết thúc
"""

import pygame  # Thư viện đồ họa và xử lý sự kiện
import ui       # Module giao diện người dùng
import player   # Module các loại người chơi (Human, Computer)
import board    # Module bảng cờ và logic game
from config import BLACK, WHITE, HUMAN  # Hằng số màu và loại người chơi
from evaluator import Evaluator          # Module đánh giá tình thế
import log      # Module ghi log

# Thiết lập logger để ghi lại thông tin debug và hoạt động game
logger = log.setup_custom_logger('root')

# Workaround cho py2exe - ẩn console khi đóng gói thành file .exe
# import sys
# import os
# sys.stdout = open(os.devnull, 'w')
# sys.stderr = open(os.devnull, 'w')


class Othello:
    """
    LỚP CHÍNH CỦA GAME OTHELLO

    Chức năng chính:
    1. Khởi tạo giao diện và các thành phần game
    2. Quản lý luồng từ menu đến gameplay
    3. Điều phối giữa các người chơi
    4. Theo dõi trạng thái game và hiển thị kết quả
    """

    def __init__(self):
        """
        KHỞI TẠO GAME
        - Tạo giao diện người dùng (GUI)
        - Tạo bảng cờ 8x8
        - Tạo module đánh giá tình thế
        - Hiển thị menu chính để người dùng chọn
        """
        self.gui = ui.Gui()               # Giao diện đồ họa với pygame
        self.board = board.Board()        # Bảng cờ 8x8 với logic game
        self.evaluator = Evaluator()      # AI đánh giá tình thế và tính xác suất thắng
        self.gui.show_menu(self.start)    # Hiển thị menu và chờ người dùng chọn

    def start(self, *args):
        """
        THIẾT LẬP GAME DỰA TRÊN LỰA CHỌN CỦA NGƯỜI DÙNG

        Args:
            player1: Loại người chơi 1 (HUMAN hoặc COMPUTER)
            player2: Loại người chơi 2 (HUMAN hoặc COMPUTER)
            level: Độ khó AI (0-7, được cộng thêm 3 để thành depth minimax)

        Luồng hoạt động:
        1. Tạo đối tượng người chơi dựa trên lựa chọn
        2. Hiển thị màn hình game
        3. Tính xác suất thắng ban đầu (50-50)
        4. Cập nhật giao diện với trạng thái đầu
        """
        player1, player2, level = args
        logger.info('Cài đặt: Người chơi 1: %s, Người chơi 2: %s, Độ khó: %s', player1, player2, level)

        # Tạo người chơi 1 (quân đen - đi trước)
        if player1 == HUMAN:
            self.now_playing = player.Human(self.gui, BLACK)  # Người chơi thật
        else:
            self.now_playing = player.Computer(BLACK, level + 3)  # AI với độ sâu minimax

        # Tạo người chơi 2 (quân trắng)
        if player2 == HUMAN:
            self.other_player = player.Human(self.gui, WHITE)
        else:
            self.other_player = player.Computer(WHITE, level + 3)

        self.gui.show_game()  # Chuyển từ menu sang màn hình chơi

        # Tính xác suất thắng ban đầu (ở vị thế khởi đầu thường là 50-50)
        black_win_prob, white_win_prob = self.evaluator.calculate_win_probability(
            self.board, BLACK, WHITE)

        # Cập nhật giao diện: bảng cờ, điểm số (2-2), người chơi hiện tại, xác suất thắng
        self.gui.update(self.board.board, 2, 2, self.now_playing.color,
                        black_win_prob, white_win_prob)

    def run(self):
        """
        VÒNG LẶP CHÍNH CỦA GAME - TRÁI TIM CỦA OTHELLO

        Luồng hoạt động chi tiết:
        1. Kiểm tra game có kết thúc chưa (không còn nước đi hợp lệ)
        2. Lấy danh sách nước đi hợp lệ cho người chơi hiện tại
        3. Nếu có nước đi: thực hiện nước đi và cập nhật giao diện
        4. Chuyển lượt cho người chơi khác
        5. Lặp lại cho đến khi game kết thúc

        Cách tính điểm: Đếm số quân đen vs trắng trên bảng
        """
        clock = pygame.time.Clock()  # Điều khiển FPS (60 frame/giây)

        while True:  # Vòng lặp game chính
            clock.tick(60)  # Giới hạn 60 FPS để game mượt mà

            # KIỂM TRA ĐIỀU KIỆN KẾT THÚC GAME
            if self.board.game_ended():
                whites, blacks, empty = self.board.count_stones()  # Đếm quân cuối game

                # XÁC ĐỊNH NGƯỜI THẮNG DỰA TRÊN SỐ QUÂN
                if whites > blacks:
                    winner = WHITE      # Trắng thắng
                elif blacks > whites:
                    winner = BLACK      # Đen thắng
                else:
                    winner = None       # Hòa
                break  # Thoát vòng lặp game

            # CẬP NHẬT TRẠNG THÁI CHO NGƯỜI CHƠI HIỆN TẠI
            self.now_playing.get_current_board(self.board)  # Đưa bảng cờ hiện tại cho người chơi

            # LẤY DANH SÁCH NƯỚC ĐI HỢP LỆ
            valid_moves = self.board.get_valid_moves(self.now_playing.color)

            # NẾU CÓ NƯỚC ĐI HỢP LỆ
            if valid_moves != []:
                # Người chơi thực hiện nước đi (Human: click chuột, Computer: minimax)
                score, self.board = self.now_playing.get_move()

                # ĐẾM LẠI QUÂN SAU NƯỚC ĐI
                whites, blacks, empty = self.board.count_stones()

                # TÍNH XÁC SUẤT THẮNG SAU NƯỚC ĐI (dùng AI đánh giá)
                black_win_prob, white_win_prob = self.evaluator.calculate_win_probability(
                    self.board, BLACK, WHITE)

                # CẬP NHẬT GIAO DIỆN với trạng thái mới
                self.gui.update(self.board.board, blacks, whites,
                                self.now_playing.color, black_win_prob, white_win_prob)

            # CHUYỂN LƯỢT: Hoán đổi người chơi hiện tại và người chơi khác
            self.now_playing, self.other_player = self.other_player, self.now_playing

        # HIỂN THỊ KẾT QUẢ CUỐI GAME
        self.gui.show_winner(winner)
        pygame.time.wait(1000)  # Chờ 1 giây để người chơi xem kết quả
        self.restart()          # Khởi động lại game

    def restart(self):
        """
        KHỞI ĐỘNG LẠI GAME
        - Tạo bảng cờ mới (trở về trạng thái ban đầu)
        - Tạo evaluator mới
        - Hiển thị menu để chọn lại
        """
        self.board = board.Board()      # Bảng cờ mới với 4 quân ở giữa
        self.evaluator = Evaluator()    # Evaluator mới
        self.gui.show_menu(self.start)  # Về menu chính
        self.run()                      # Bắt đầu vòng lặp game mới


def main():
    """
    HÀM CHÍNH - ĐIỂM KHỞI ĐẦU CHƯƠNG TRÌNH
    Tạo đối tượng game và bắt đầu chạy
    """
    game = Othello()  # Tạo game mới
    game.run()        # Bắt đầu vòng lặp chính


if __name__ == '__main__':
    main()  # Chạy game khi file được thực thi trực tiếp
