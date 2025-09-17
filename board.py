#!/usr/bin/env python
"""
board.py Humberto Henrique Campos Pinheiro
LOGIC CHÍNH CỦA GAME OTHELLO

File này chứa tất cả các quy tắc và logic của game:
- Khởi tạo bảng cờ 8x8 với 4 quân ở giữa
- Tìm nước đi hợp lệ
- Thực hiện nước đi và lật quân
- Kiểm tra kết thúc game
- Tính điểm (đếm quân)
"""

from config import WHITE, BLACK, EMPTY  # Hằng số màu quân cờ
from copy import deepcopy               # Sao chép sâu để tạo bản copy board


class Board:

    """
    LỚP BOARD - CHỨA TẤT CẢ LOGIC VÀ QUY TẮC CỦA OTHELLO

    Chức năng chính:
    1. Quản lý trạng thái bảng cờ 8x8
    2. Tìm và xác thực nước đi hợp lệ
    3. Thực hiện nước đi và lật quân theo quy tắc Othello
    4. Kiểm tra điều kiện kết thúc game
    5. Tính toán điểm số và thống kê
    """

    def __init__(self):
        """
        KHỞI TẠO BẢNG CỜ OTHELLO CHUẨN
        - Tạo bảng 8x8 với tất cả ô trống (0)
        - Đặt 4 quân ở giữa theo vị trí chuẩn Othello:
          [3,3] = Trắng    [3,4] = Đen
          [4,3] = Đen      [4,4] = Trắng
        """
        # Tạo bảng cờ 8x8 rỗng (tất cả ô = 0 = EMPTY)
        self.board = [[0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0]]

        # Thiết lập vị trí khởi đầu chuẩn của Othello (4 quân ở giữa)
        self.board[3][4] = BLACK  # Đen ở [3,4]
        self.board[4][3] = BLACK  # Đen ở [4,3]
        self.board[3][3] = WHITE  # Trắng ở [3,3]
        self.board[4][4] = WHITE  # Trắng ở [4,4]

        self.valid_moves = []  # Danh sách nước đi hợp lệ (được cập nhật mỗi lượt)

    def __getitem__(self, i, j):
        """Truy cập phần tử board[i][j] - hỗ trợ cú pháp board[i,j]"""
        return self.board[i][j]

    def lookup(self, row, column, color):
        """
        TÌM CÁC VỊ TRÍ CÓ THỂ ĐẶT QUÂN TỪ MỘT QUÂN CHỜ SẴN

        Thuật toán:
        1. Từ quân cờ tại (row, column) với màu 'color'
        2. Tìm theo 8 hướng (ngang, dọc, chéo)
        3. Nếu có ít nhất 1 quân đối phương liền kề
        4. Và cuối cùng có ô trống -> đó là nước đi hợp lệ

        Args:
            row, column: Vị trí quân cờ hiện tại
            color: Màu quân (BLACK hoặc WHITE)

        Returns:
            List các vị trí (row, col) có thể đặt quân
        """
        # Xác định màu đối phương
        if color == BLACK:
            other = WHITE
        else:
            other = BLACK

        places = []  # Danh sách vị trí có thể đặt quân

        # Kiểm tra vị trí hợp lệ (trong bảng 8x8)
        if row < 0 or row > 7 or column < 0 or column > 7:
            return places

        # Kiểm tra theo 8 hướng từ vị trí hiện tại
        # (-1,0)=Bắc, (-1,1)=Đông Bắc, (0,1)=Đông, (1,1)=Đông Nam
        # (1,0)=Nam, (1,-1)=Tây Nam, (0,-1)=Tây, (-1,-1)=Tây Bắc
        for (x, y) in [
                (-1, 0),   # Bắc
                (-1, 1),   # Đông Bắc
                (0, 1),    # Đông
                (1, 1),    # Đông Nam
                (1, 0),    # Nam
                (1, -1),   # Tây Nam
                (0, -1),   # Tây
                (-1, -1)   # Tây Bắc
            ]:
            # Kiểm tra hướng này có vị trí hợp lệ không
            pos = self.check_direction(row, column, x, y, other)
            if pos:
                places.append(pos)
        return places

    def check_direction(self, row, column, row_add, column_add, other_color):
        """
        KIỂM TRA MỘT HƯỚNG CỤ THỂ CÓ VỊ TRÍ HỢP LỆ KHÔNG

        Thuật toán:
        1. Bắt đầu từ vị trí hiện tại, di chuyển theo hướng (row_add, column_add)
        2. Phải có ít nhất 1 quân đối phương ở ô kế tiếp
        3. Tiếp tục đi cho đến khi gặp ô trống hoặc quân cùng màu
        4. Nếu ô cuối là ô trống -> đây là nước đi hợp lệ

        Returns:
            (i, j) nếu tìm thấy vị trí hợp lệ, None nếu không
        """
        i = row + row_add      # Vị trí hàng tiếp theo
        j = column + column_add # Vị trí cột tiếp theo

        # Bước 1: Kiểm tra ô đầu tiên có phải là quân đối phương không
        if (i >= 0 and j >= 0 and i < 8 and j < 8 and self.board[i][j] == other_color):
            # Bước 2: Tiếp tục đi qua tất cả quân đối phương liên tiếp
            i += row_add
            j += column_add
            while (i >= 0 and j >= 0 and i < 8 and j < 8 and self.board[i][j] == other_color):
                i += row_add
                j += column_add

            # Bước 3: Kiểm tra ô cuối có trống không (nước đi hợp lệ)
            if (i >= 0 and j >= 0 and i < 8 and j < 8 and self.board[i][j] == EMPTY):
                return (i, j)  # Trả về vị trí có thể đặt quân

    def get_valid_moves(self, color):
        """
        TÌM TẤT CẢ NƯỚC ĐI HỢP LỆ CHO MỘT MÀU QUÂN

        Đây là hàm quan trọng nhất trong logic Othello:
        1. Duyệt qua tất cả quân cùng màu trên bảng
        2. Từ mỗi quân, tìm các vị trí có thể đặt quân mới
        3. Loại bỏ các vị trí trùng lặp
        4. Lưu vào self.valid_moves để sử dụng sau

        QUAN TRỌNG: Phải gọi hàm này trước khi gọi apply_move()

        Args:
            color: Màu quân cần tìm nước đi (BLACK hoặc WHITE)

        Returns:
            List các vị trí (row, col) có thể đặt quân
        """
        # Xác định màu đối phương
        if color == BLACK:
            other = WHITE
        else:
            other = BLACK

        places = []  # Danh sách nước đi hợp lệ

        # Duyệt qua toàn bộ bảng cờ 8x8
        for i in range(8):
            for j in range(8):
                # Nếu tìm thấy quân cùng màu
                if self.board[i][j] == color:
                    # Tìm tất cả vị trí hợp lệ từ quân này
                    places = places + self.lookup(i, j, color)

        # Loại bỏ các vị trí trùng lặp (dùng set rồi chuyển về list)
        places = list(set(places))
        self.valid_moves = places  # Lưu lại để apply_move() sử dụng
        return places

    def apply_move(self, move, color):
        """
        THỰC HIỆN NƯỚC ĐI VÀ LẬT QUÂN THEO QUY TẮC OTHELLO

        Quy trình:
        1. Kiểm tra nước đi có hợp lệ không (phải nằm trong valid_moves)
        2. Đặt quân vào vị trí được chọn
        3. Lật tất cả quân đối phương theo 8 hướng

        Args:
            move: Tuple (row, col) vị trí muốn đặt quân
            color: Màu quân (BLACK hoặc WHITE)
        """
        # Kiểm tra nước đi hợp lệ
        if move in self.valid_moves:
            # Đặt quân vào vị trí được chọn
            self.board[move[0]][move[1]] = color

            # Lật quân theo 8 hướng (1=Bắc, 2=ĐB, 3=Đông, ..., 8=TB)
            for i in range(1, 9):
                self.flip(i, move, color)

    def flip(self, direction, position, color):
        """
        LẬT QUÂN THEO MỘT HƯỚNG CỤ THỂ - TRÁI TIM CỦA OTHELLO

        Đây là quy tắc quan trọng nhất của Othello:
        1. Từ vị trí vừa đặt quân, đi theo hướng được chỉ định
        2. Tìm tất cả quân đối phương liên tiếp
        3. Nếu cuối chuỗi là quân cùng màu -> lật toàn bộ chuỗi

        Args:
            direction: Hướng (1=Bắc, 2=ĐB, 3=Đông, 4=ĐN, 5=Nam, 6=TN, 7=Tây, 8=TB)
            position: Vị trí vừa đặt quân (row, col)
            color: Màu quân vừa đặt
        """
        # Xác định vector di chuyển theo hướng
        if direction == 1:
            # Bắc: lên trên
            row_inc = -1
            col_inc = 0
        elif direction == 2:
            # Đông Bắc: lên trên, sang phải
            row_inc = -1
            col_inc = 1
        elif direction == 3:
            # Đông: sang phải
            row_inc = 0
            col_inc = 1
        elif direction == 4:
            # Đông Nam: xuống dưới, sang phải
            row_inc = 1
            col_inc = 1
        elif direction == 5:
            # Nam: xuống dưới
            row_inc = 1
            col_inc = 0
        elif direction == 6:
            # Tây Nam: xuống dưới, sang trái
            row_inc = 1
            col_inc = -1
        elif direction == 7:
            # Tây: sang trái
            row_inc = 0
            col_inc = -1
        elif direction == 8:
            # Tây Bắc: lên trên, sang trái
            row_inc = -1
            col_inc = -1

        places = []  # Danh sách quân sẽ bị lật
        i = position[0] + row_inc  # Vị trí hàng tiếp theo
        j = position[1] + col_inc  # Vị trí cột tiếp theo

        # Xác định màu đối phương
        if color == WHITE:
            other = BLACK
        else:
            other = WHITE

        # Kiểm tra ô đầu tiên có phải là quân đối phương không
        if i in range(8) and j in range(8) and self.board[i][j] == other:
            # Có ít nhất 1 quân đối phương để lật
            places = places + [(i, j)]
            i = i + row_inc
            j = j + col_inc

            # Tiếp tục tìm thêm quân đối phương
            while i in range(8) and j in range(8) and self.board[i][j] == other:
                places = places + [(i, j)]
                i = i + row_inc
                j = j + col_inc

            # Kiểm tra cuối chuỗi có phải quân cùng màu không
            if i in range(8) and j in range(8) and self.board[i][j] == color:
                # Tìm thấy quân cùng màu -> lật tất cả quân ở giữa
                for pos in places:
                    self.board[pos[0]][pos[1]] = color  # Lật quân

    def get_changes(self):
        """
        TRẢ VỀ TRẠNG THÁI BẢNG Cờ VÀ ĐIỂM SỐ
        Sử dụng cho việc cập nhật giao diện

        Returns:
            tuple (board, blacks, whites): Bảng cờ và điểm số 2 bên
        """
        whites, blacks, empty = self.count_stones()  # Đếm quân
        return (self.board, blacks, whites)  # Trả về (bảng, đen, trắng)

    def game_ended(self):
        """
        KIỂM TRA GAME ĐÃ KẾT THÚC CHƯA - 3 ĐIỀU KIỆN

        Game kết thúc khi:
        1. Bảng đầy (đầy 64 quân)
        2. Một bên bị tiêu diệt hết quân (0 quân)
        3. Cả 2 bên đều không có nước đi hợp lệ

        Returns:
            bool: True nếu game kết thúc, False nếu vẫn tiếp tục
        """
        # Đếm quân hiện tại
        whites, blacks, empty = self.count_stones()

        # Điều kiện 1&2: Bảng đầy hoặc một bên bị tiêu diệt
        if whites == 0 or blacks == 0 or empty == 0:
            return True

        # Điều kiện 3: Cả 2 bên đều hết nước đi
        if self.get_valid_moves(BLACK) == [] and \
           self.get_valid_moves(WHITE) == []:
            return True

        return False  # Game vẫn tiếp tục

    def print_board(self):
        """
        IN BẢNG Cờ RA CONSOLE - DÀNH CHO DEBUG
        Hiển thị: B = quân đen, W = quân trắng, khoảng trống = ô trống
        """
        for i in range(8):
            print(i, ' |', end=' ')  # Số thứ tự hàng
            for j in range(8):
                if self.board[i][j] == BLACK:
                    print('B', end=' ')  # Quân đen
                elif self.board[i][j] == WHITE:
                    print('W', end=' ')  # Quân trắng
                else:
                    print(' ', end=' ')  # Ô trống
                print('|', end=' ')     # Ngăn cách
            print()  # Xuống dòng

    def count_stones(self):
        """
        ĐẾM QUÂN - CÁCH TÍNH ĐIỂM TRONG OTHELLO

        Điểm số trong Othello rất đơn giản:
        - Mỗi quân trên bảng = 1 điểm
        - Không có trọng số đặc biệt cho vị trí nào
        - Ai có nhiều quân hơn thì thắng

        Returns:
            tuple (whites, blacks, empty): Số quân trắng, đen, ô trống
        """
        whites = 0  # Số quân trắng
        blacks = 0  # Số quân đen
        empty = 0   # Số ô trống

        # Duyệt toàn bảng để đếm
        for i in range(8):
            for j in range(8):
                if self.board[i][j] == WHITE:
                    whites += 1
                elif self.board[i][j] == BLACK:
                    blacks += 1
                else:
                    empty += 1
        return whites, blacks, empty

    def compare(self, otherBoard):
        """
        SO SÁNH 2 BẢNG Cờ - TÌM KHAC BIỆT
        (Chức năng hỗ trợ, ít được sử dụng)

        Tìm các ô khác nhau giữa 2 bảng
        Có vẻ là có bug: return otherBoard thay vì diffBoard

        Args:
            otherBoard: Bảng cờ khác để so sánh

        Returns:
            Board chứa các ô khác biệt
        """
        diffBoard = Board()  # Tạo bảng mới
        # Xóa các quân khởi đầu (làm trống bảng)
        diffBoard.board[3][4] = 0
        diffBoard.board[3][3] = 0
        diffBoard.board[4][3] = 0
        diffBoard.board[4][4] = 0

        # Tìm các ô khác nhau
        for i in range(8):
            for j in range(8):
                if otherBoard.board[i][j] != self.board[i][j]:
                    diffBoard.board[i][j] = otherBoard.board[i][j]

        return otherBoard  # BUG: nên return diffBoard

    def get_adjacent_count(self, color):
        """
        ĐẾM SỐ Ô TRỐNG KỀ BÊN QUÂN CÙNG MÀU
        Được sử dụng trong đánh giá AI - quan trọng cho chiến thuật

        Ô kề bên nhiều = linh hoạt cao, có thể phát triển
        Ô kề bên ít = ổn định nhưng khó mở rộng

        Args:
            color: Màu quân cần kiểm tra

        Returns:
            int: Số ô trống kề bên quân cùng màu
        """
        adjCount = 0

        # Tìm tất cả quân cùng màu trên bảng
        for x, y in [(a, b) for a in range(8) for b in range(8) if self.board[a][b] == color]:
            # Kiểm tra 8 ô xung quanh mỗi quân
            for i, j in [(a, b) for a in [-1, 0, 1] for b in [-1, 0, 1]]:
                # Bỏ qua ô trung tâm (i=0, j=0)
                if i == 0 and j == 0:
                    continue
                # Kiểm tra trong giới hạn bảng
                if 0 <= x + i <= 7 and 0 <= y + j <= 7:
                    # Nếu ô kề bên là ô trống
                    if self.board[x + i][y + j] == EMPTY:
                        adjCount += 1
        return adjCount

    def next_states(self, color):
        """
        TẠO TẤT CẢ BẢNG Cờ CÓ THỂ SAU 1 NƯỚC ĐI - CHO MINIMAX AI

        Đây là generator (iterator) hiệu quả:
        1. Lấy tất cả nước đi hợp lệ
        2. Với mỗi nước đi:
           - Tạo bản copy của bảng hiện tại
           - Thực hiện nước đi trên bản copy
           - Yield bảng mới (không lưu hết vào memory)

        Sử dụng trong minimax để duyệt tất cả khả năng

        Args:
            color: Màu người chơi

        Yields:
            Board: Các trạng thái bảng sau mỗi nước đi có thể
        """
        valid_moves = self.get_valid_moves(color)  # Lấy nước đi hợp lệ
        for move in valid_moves:
            newBoard = deepcopy(self)          # Tạo bản copy
            newBoard.apply_move(move, color)   # Thực hiện nước đi
            yield newBoard                     # Trả về bảng mới
