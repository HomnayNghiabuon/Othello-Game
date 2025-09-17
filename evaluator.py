"""
evaluator.py - BỘ ĐÁNH GIÁ TÌNH THẾ VÀ TÍNH ĐIỂM OTHELLO

File này chứa trái tim AI của game - các thuật toán đánh giá:
1. Đếm quân (piece count)
2. Kiểm soát góc (corner control)
3. Kiểm soát cạnh (edge control)
4. Tính linh hoạt (mobility)
5. X-squares (ô nguy hiểm gần góc)
6. Tính xác suất thắng

Công thức tính điểm được điều chỉnh theo 5 giai đoạn game dựa trên số quân:
- Band 0: 0-16 quân (đầu game)
- Band 1: 17-32 quân
- Band 2: 33-48 quân
- Band 3: 49-64 quân (cuối game)
- Band 4: Endgame hoàn toàn
"""

from config import BLACK, WHITE, EMPTY


class Evaluator(object):
    """
    BỘ ĐÁNH GIÁ TÌNH THẾ OTHELLO - TRÁI TIM CỦA AI

    Các trọng số được tinh chỉnh qua nhiều lần thử nghiệm:
    - Số càng lớn = quan trọng hơn
    - Số âm = bất lợi
    - Index [0,1,2,3,4] tương ứng với band 0-4 (giai đoạn game)
    """

    # Điểm cực đại khi đối phương hết quân (thắng tuyệt đối)
    WIPEOUT_SCORE = 1000

    # Trọng số đếm quân - chỉ quan trọng cuối game
    PIECE_COUNT_WEIGHT = [0, 0, 0, 4, 1]

    # Trọng số tính linh hoạt tiềm năng (số ô trống kề bên)
    POTENTIAL_MOBILITY_WEIGHT = [5, 4, 3, 2, 0]

    # Trọng số số nước đi hợp lệ - rất quan trọng đầu/giữa game
    MOBILITY_WEIGHT = [7, 6, 5, 4, 0]

    # Trọng số kiểm soát góc - cực kỳ quan trọng mọi giai đoạn
    CORNER_WEIGHT = [35, 35, 35, 35, 0]

    # Trọng số kiểm soát cạnh
    EDGE_WEIGHT = [0, 3, 4, 5, 0]

    # Trọng số X-squares (ô nguy hiểm gần góc) - bất lợi
    XSQUARE_WEIGHT = [-8, -8, -8, -8, 0]

    def get_piece_differential(self, deltaBoard, band):
        """
        TÍNH CHÊNH LỆCH SỐ QUÂN - CÔNG THỨC ĐIỂM CƠ BẢN NHẤT

        Othello: Ai có nhiều quân hơn thì thắng!
        Nhưng chỉ quan trọng ở cuối game (band 3-4)
        Đầu game không nên quá chú trọng vào số quân

        Args:
            deltaBoard: Bảng chênh lệch (quân mới được thêm/lật)
            band: Giai đoạn game (0-4)

        Returns:
            int: Điểm số dựa trên chênh lệch quân (tôi - đối thủ)
        """
        if Evaluator.PIECE_COUNT_WEIGHT[band] != 0:
            whites, blacks, empty = deltaBoard.count_stones()

            # Xác định quân của tôi vs đối thủ
            if self.player == WHITE:
                myScore = whites      # Tôi là trắng
                yourScore = blacks    # Đối thủ là đen
            else:
                myScore = blacks      # Tôi là đen
                yourScore = whites    # Đối thủ là trắng

            # Tính điểm = trọng số × (quân tôi - quân đối thủ)
            return Evaluator.PIECE_COUNT_WEIGHT[band] * (myScore - yourScore)
        return 0

    def get_corner_differential(self, deltaCount, deltaBoard, band):
        """
        TÍNH CHÊNH LỆCH KIỂM SOÁT GÓC - CỰC KỲ QUAN TRỌNG!

        4 góc của bảng cờ: (0,0), (0,7), (7,0), (7,7)
        Góc = vị trí không thể bị lật lại = ưu thế tuyệt đối
        Ai chiếm được nhiều góc có lợi thế rất lớn

        Tại sao góc quan trọng:
        - Không bao giờ bị lật
        - Tạo 'anchor' để xây dựng hàng cạnh an toàn
        - Hạn chế di chuyển của đối thủ

        Args:
            deltaCount: Tổng số quân thay đổi
            deltaBoard: Bảng chênh lệch
            band: Giai đoạn game

        Returns:
            int: Điểm góc (trọng số cao = 35 điểm/góc)
        """
        if Evaluator.CORNER_WEIGHT[band] != 0:
            myScore = 0    # Số góc tôi chiếm
            yourScore = 0  # Số góc đối thủ chiếm

            # Kiểm tra 4 góc: (0,0), (0,7), (7,0), (7,7)
            for i in [0, 7]:        # Hàng đầu và cuối
                for j in [0, 7]:    # Cột đầu và cuối
                    if deltaBoard.board[i][j] == self.player:
                        myScore += 1
                    elif deltaBoard.board[i][j] == self.enemy:
                        yourScore += 1

                    # Tối ưu: dừng sớm khi đã đếm đủ
                    if myScore + yourScore >= deltaCount:
                        break
                if myScore + yourScore >= deltaCount:
                    break

            # Tính điểm = 35 × (góc tôi - góc đối thủ)
            return Evaluator.CORNER_WEIGHT[band] * (myScore - yourScore)
        return 0

    def get_edge_differential(self, deltaCount, deltaBoard, band):
        """
        TÍNH CHÊNH LỆCH KIỂM SOÁT CẠNH - QUAN TRỌNG TRUNG BÌNH

        Cạnh = 4 cạnh của bảng cờ (không tính góc)
        Vị trí cạnh tương đối ổn định, khó bị tấn công

        Bao gồm:
        - Hàng trên/dưới: (0,1-6) và (7,1-6)
        - Cột trái/phải: (1-6,0) và (1-6,7)

        Tại sao cạnh quan trọng:
        - Ít bị tấn công hơn ô giữa
        - Tạo nền tảng cho việc chiếm góc
        - Hạn chế tùy chọn của đối thủ

        Args:
            deltaCount: Số quân thay đổi
            deltaBoard: Bảng chênh lệch
            band: Giai đoạn game

        Returns:
            int: Điểm cạnh (trọng số 0-5 tùy giai đoạn)
        """
        if Evaluator.EDGE_WEIGHT[band] != 0:
            myScore = 0    # Số ô cạnh tôi chiếm
            yourScore = 0  # Số ô cạnh đối thủ chiếm

            # Tạo danh sách tất cả ô cạnh (không tính góc)
            # Hàng trên/dưới: (0,1-6) và (7,1-6)
            # Cột trái/phải: (1-6,0) và (1-6,7)
            squares = [(a, b) for a in [0, 7] for b in range(1, 7)] + \
                     [(a, b) for a in range(1, 7) for b in [0, 7]]

            # Đếm ô cạnh của mỗi bên
            for x, y in squares:
                if deltaBoard.board[x][y] == self.player:
                    myScore += 1
                elif deltaBoard.board[x][y] == self.enemy:
                    yourScore += 1

                # Tối ưu: dừng sớm
                if myScore + yourScore >= deltaCount:
                    break

            # Tính điểm cạnh
            return Evaluator.EDGE_WEIGHT[band] * (myScore - yourScore)
        return 0

    def get_xsquare_differential(self, startBoard, currentBoard, deltaBoard, band):
        """
        TÍNH ĐIỂM X-SQUARES - Ô NGUY HIỂM GẦN GÓC (BẤT LỢI!)

        X-squares là 4 ô ngay bên cạnh góc: (1,1), (1,6), (6,1), (6,6)
        Tại sao nguy hiểm:
        - Nếu đặt quân vào X-square khi góc chưa bị chiếm
        - Đối thủ có thể dễ dàng chiếm góc đó!
        - Vì vậy X-square có điểm âm (-8)

        Chỉ tính X-squares mới được đặt (không tính quân bị lật)
        Chỉ tính khi góc tương ứng vẫn trống

        Args:
            startBoard: Bảng trước nước đi
            currentBoard: Bảng sau nước đi
            deltaBoard: Bảng chênh lệch
            band: Giai đoạn game

        Returns:
            int: Điểm X-square (âm = bất lợi)
        """
        if Evaluator.XSQUARE_WEIGHT[band] != 0:
            myScore = 0    # X-squares tôi tạo (bất lợi)
            yourScore = 0  # X-squares đối thủ tạo (lợi cho tôi)

            # Kiểm tra 4 X-squares: (1,1), (1,6), (6,1), (6,6)
            for x, y in [(a, b) for a in [1, 6] for b in [1, 6]]:
                # Chỉ tính quân mới được đặt (không phải bị lật)
                if deltaBoard.board[x][y] != EMPTY and startBoard.board[x][y] == EMPTY:

                    # Tìm góc tương ứng với X-square này
                    cornerx = x
                    cornery = y
                    if cornerx == 1:
                        cornerx = 0  # X-square (1,*) -> góc (0,*)
                    elif cornerx == 6:
                        cornerx = 7  # X-square (6,*) -> góc (7,*)
                    if cornery == 1:
                        cornery = 0  # X-square (*,1) -> góc (*,0)
                    elif cornery == 6:
                        cornery = 7  # X-square (*,6) -> góc (*,7)

                    # Chỉ tính khi góc vẫn trống (chưa ai chiếm)
                    if currentBoard.board[cornerx][cornery] == EMPTY:
                        if currentBoard.board[x][y] == self.player:
                            myScore += 1    # Tôi tạo X-square = bất lợi
                        elif currentBoard.board[x][y] == self.enemy:
                            yourScore += 1  # Đối thủ tạo = lợi cho tôi

            # Điểm âm vì X-square là bất lợi
            return Evaluator.XSQUARE_WEIGHT[band] * (myScore - yourScore)
        return 0

    def get_potential_mobility_differential(self, startBoard, currentBoard, band):
        """
        TÍNH LINH HOẠT TIỀM NĂNG - SỐ Ô TRỐNG KỀ BÊN

        Linh hoạt tiềm năng = số ô trống kề bên quân của mình
        - Ô kề bên nhiều = có thể phát triển nhiều hướng
        - Ô kề bên ít = bị hạn chế, khô mở rộng

        Lưu ý đặc biệt: Công thức ngược!
        - myScore = thay đổi ô kề bên của ĐốI THỦ
        - yourScore = thay đổi ô kề bên của TÔI

        Tại sao ngược? Vì muốn giảm ô kề bên của đối thủ (hạn chế họ)

        Args:
            startBoard: Bảng trước nước đi
            currentBoard: Bảng sau nước đi
            band: Giai đoạn game

        Returns:
            int: Điểm linh hoạt tiềm năng
        """
        if Evaluator.POTENTIAL_MOBILITY_WEIGHT[band] != 0:
            # Thay đổi ô kề bên của đối thủ (muốn giảm = tốt)
            myScore = currentBoard.get_adjacent_count(self.enemy) - \
                     startBoard.get_adjacent_count(self.enemy)

            # Thay đổi ô kề bên của tôi (muốn giảm ít = tốt)
            yourScore = currentBoard.get_adjacent_count(self.player) - \
                       startBoard.get_adjacent_count(self.player)

            # Công thức: (giảm của đối thủ) - (giảm của tôi) = điểm tốt
            return Evaluator.POTENTIAL_MOBILITY_WEIGHT[band] * (myScore - yourScore)
        return 0

    def get_mobility_differential(self, startBoard, currentBoard, band):
        """
        TÍNH LINH HOẠT THỰC TẾ - SỐ NƯỚC ĐI HỢP LỆ

        Đây là yếu tố CỰC KỲ QUAN TRỌNG trong Othello!
        - Nhiều nước đi = linh hoạt, tùy chọn nhiều
        - Ít nước đi = bị hạn chế, dễ bị ép buộc
        - Không có nước đi = bị bỏ lượt!

        Trọng số cao nhất ở đầu game (band 0 = 7 điểm)
        Cuối game không quan trọng (band 4 = 0 điểm)

        Args:
            startBoard: Bảng trước nước đi
            currentBoard: Bảng sau nước đi
            band: Giai đoạn game

        Returns:
            int: Điểm linh hoạt (thường là điểm cao nhất)
        """
        # Sự thay đổi nước đi hợp lệ của tôi
        myScore = len(currentBoard.get_valid_moves(self.player)) - \
                  len(startBoard.get_valid_moves(self.player))

        # Sự thay đổi nước đi hợp lệ của đối thủ
        yourScore = len(currentBoard.get_valid_moves(self.enemy)) - \
                   len(startBoard.get_valid_moves(self.enemy))

        # Điểm = (tăng của tôi - giảm của tôi) - (tăng của đối thủ - giảm của đối thủ)
        return Evaluator.MOBILITY_WEIGHT[band] * (myScore - yourScore)

    def score(self, startBoard, board, currentDepth, player, opponent):
        """
        HÀM TÍNH ĐIỂM CHÍNH - TRÁI TIM CỦA AI OTHELLO

        Đây là hàm quan trọng nhất, quyết định AI chơi thông minh như thế nào!
        Kết hợp 6 tiêu chí đánh giá với trọng số khác nhau theo giai đoạn

        Quy trình:
        1. Kiểm tra điều kiện thắng tuyệt đối (wipeout)
        2. Xác định giai đoạn game (band 0-4)
        3. Tính điểm theo 6 tiêu chí
        4. Trả về tổng điểm cuối cùng

        Args:
            startBoard: Bảng gốc (trước khi đánh giá)
            board: Bảng cần đánh giá
            currentDepth: Độ sâu hiện tại trong cây minimax
            player: Màu người chơi đang đánh giá
            opponent: Màu đối thủ

        Returns:
            int: Điểm tổng hợp (dương = lợi thế, âm = bất lợi)
        """
        self.player = player    # Lưu màu người chơi
        self.enemy = opponent   # Lưu màu đối thủ
        sc = 0                  # Điểm số tổng hợp

        # Đếm quân hiện tại
        whites, blacks, empty = board.count_stones()
        deltaBoard = board.compare(startBoard)      # Bảng chênh lệch
        deltaCount = sum(deltaBoard.count_stones())  # Số quân thay đổi

        # KIỂM TRA ĐIỀU KIỆN THẮNG TUYỆT ĐỐI (1000 điểm!)
        if (self.player == WHITE and whites == 0) or (self.player == BLACK and blacks == 0):
            return -Evaluator.WIPEOUT_SCORE  # Tôi bị tiêu diệt = -1000
        if (self.enemy == WHITE and whites == 0) or (self.enemy == BLACK and blacks == 0):
            return Evaluator.WIPEOUT_SCORE   # Đối thủ bị tiêu diệt = +1000

        # XÁC ĐỊNH GIAI ĐOẠN GAME (BAND) - QUYẾT ĐỊNH TRỌNG SỐ
        piece_count = whites + blacks
        band = 0
        if piece_count <= 16:
            band = 0    # Đầu game: Tập trung linh hoạt, góc
        elif piece_count <= 32:
            band = 1    # Giữa game sớm
        elif piece_count <= 48:
            band = 2    # Giữa game muộn
        elif piece_count <= 64 - currentDepth:
            band = 3    # Gần cuối game: Bắt đầu quan tâm điểm số
        else:
            band = 4    # Cuối game: Chỉ quan tâm điểm số

        # TÍNH ĐIỂM THEO 6 TIÊU CHÍ (CỘNG DỒN)
        sc += self.get_piece_differential(deltaBoard, band)              # 1. Số quân
        sc += self.get_corner_differential(deltaCount, deltaBoard, band)  # 2. Góc
        sc += self.get_edge_differential(deltaCount, deltaBoard, band)    # 3. Cạnh
        sc += self.get_xsquare_differential(startBoard, board, deltaBoard, band)  # 4. X-square
        sc += self.get_potential_mobility_differential(startBoard, board, band)   # 5. Linh hoạt tiềm năng
        sc += self.get_mobility_differential(startBoard, board, band)     # 6. Linh hoạt thực tế

        return sc  # Trả về điểm tổng hợp

    def calculate_win_probability(self, board, player, opponent, depth=3):
        """
        TÍNH XÁC SUẤT THẮNG - ĐỆM HẮTU CHO NGƯỜI DÙNG

        Kết hợp nhiều yếu tố để dự đoán tỉ lệ thắng:
        1. Điểm số Minimax (AI đánh giá chiến thuật)
        2. Số quân hiện tại
        3. Số nước đi hợp lệ (linh hoạt)
        4. Số góc kiểm soát
        5. Giai đoạn game (đầu/giữa/cuối)

        Công thức kết hợp sigmoid giúp chuyển điểm số thành %

        Args:
            board: Bảng cờ hiện tại
            player: Người chơi để tính xác suất
            opponent: Đối thủ
            depth: Độ sâu đánh giá

        Returns:
            tuple: (xác_suất_thắng_player, xác_suất_thắng_opponent)
                  Các giá trị từ 0.05 đến 0.95 (5% đến 95%)
        """
        from minimax import Minimax

        # 1. TÍNH ĐIỂM SỐ MINIMAX (chiến thuật AI)
        current_score = self.score(board, board, depth, player, opponent)

        # 2. THỐNG KÊ CƠ BẢN
        whites, blacks, empty = board.count_stones()
        total_pieces = whites + blacks

        # 3. ĐẾM NƯỚC ĐI HỢP LỆ (linh hoạt)
        player_moves = len(board.get_valid_moves(player))
        opponent_moves = len(board.get_valid_moves(opponent))

        # 4. ĐẾM GÓC KIỂM SOÁT
        player_corners = 0
        opponent_corners = 0
        for i in [0, 7]:
            for j in [0, 7]:
                if board.board[i][j] == player:
                    player_corners += 1
                elif board.board[i][j] == opponent:
                    opponent_corners += 1

        # 5. ĐẾM QUÂN CỦA MỖI BÊN
        if player == WHITE:
            player_pieces = whites
            opponent_pieces = blacks
        else:
            player_pieces = blacks
            opponent_pieces = whites

        # 6. TÍNH CÁC CHỈ SỐ LỢI THẾ (-1 đến +1)
        piece_advantage = (player_pieces - opponent_pieces) / max(total_pieces, 1)
        mobility_advantage = (player_moves - opponent_moves) / max(player_moves + opponent_moves, 1)
        corner_advantage = (player_corners - opponent_corners) / 4.0

        # 7. TRỌNG SỐ THEO GIAI ĐOẠN GAME
        if total_pieces < 20:    # Đầu game: Linh hoạt quan trọng
            score_factor = 0.3 * piece_advantage + 0.4 * mobility_advantage + 0.3 * corner_advantage
        elif total_pieces < 40:  # Giữa game: Cân bằng
            score_factor = 0.4 * piece_advantage + 0.3 * mobility_advantage + 0.3 * corner_advantage
        else:                    # Cuối game: Số quân quyết định
            score_factor = 0.6 * piece_advantage + 0.2 * mobility_advantage + 0.2 * corner_advantage

        # 8. KẾT HỢP ĐIỂM MINIMAX VÀ ĐIỂM THỐNG KÊ
        normalized_score = current_score / 1000.0  # Chuẩn hóa điểm Minimax
        combined_score = 0.7 * score_factor + 0.3 * normalized_score

        # 9. CHUYỂN THÀNH TỈ LỆ % BẰNG HÀM SIGMOID
        import math
        probability = 1 / (1 + math.exp(-combined_score * 5))

        # 10. GIỚI HẠN 5%-95% (để tránh hiển thị 0% hoặc 100%)
        player_win_prob = max(0.05, min(0.95, probability))
        opponent_win_prob = 1 - player_win_prob

        return player_win_prob, opponent_win_prob
