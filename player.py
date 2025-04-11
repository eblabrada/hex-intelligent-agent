import time
from collections import deque
from board import HexBoard
import random

class Player:
  def __init__(self, player_id: int):
    self.player_id = player_id  # Tu identificador (1 o 2)

  def play(self, board: HexBoard) -> tuple:
    raise NotImplementedError("¡Implementa este método!")

class DSU: 
  def __init__(self, N: int):
    self.INF = 10**18
    self.par = [i for i in range(N)]
    self.size = [1 for _ in range(N)]
    self.stk = [[]]
    self.best = [(self.INF, self.INF) for _ in range(N)]

  def get(self, x):
    if x == self.par[x]:
      return x
    return self.get(self.par[x])

  def sameSet(self, x, y):
    return self.get(x) == self.get(y)
  
  def save(self, x, sz, par, best):
    self.stk[-1].append((x, sz, par, best))
  
  def checkpoint(self):
    self.stk.append([])

  def rollback(self):
    while len(self.stk[-1]) > 0:
      x, sz, par, best = self.stk[-1].pop()
      self.size[x], self.par[x], self.best[x] = sz, par, best
    self.stk.pop()

  def unite(self, x, y):
    x, y = self.get(x), self.get(y)
    if x != y:
      if self.size[x] < self.size[y]:
        x, y = y, x
      self.save(x, self.size[x], self.par[x], self.best[x])
      self.save(y, self.size[y], self.par[y], self.best[y])
      self.par[y] = x; self.size[x] += self.size[y]
      self.best[x] = min(self.best[x][0], self.best[y][0]), min(self.best[x][1], self.best[y][1])
      return True
    return False

class PopPlayer(Player):
  def __init__(self, player_id: int):
    self.player_id = player_id
    self.directions = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, 1), (1, -1)]
    self.INF = 10**18
    
  def play(self, board: HexBoard, time_limit = 10.0) -> tuple:
    time_limit -= 2.0
    start_time = time.time()
    N = board.size ** 2 # number of vertex of board graph
    
    def encode(x, y):
      return x * board.size + y
      
    def decode(value):
      return (value // board.size, value % board.size)

    def inside(x, y):
      return x >= 0 and x < board.size and y >= 0 and y < board.size

    def bfs_multisource_player1(cur_board: HexBoard, column: int):
      best = [self.INF for _ in range(N)]
      dp = [0 for _ in range(N)]
      dq = deque()
      for row in range(cur_board.size):
        if cur_board.board[row][column] == 0:
          best[encode(row, column)] = 1
          dp[encode(row, column)] = 1
          dq.append((1, row, column))
        elif cur_board.board[row][column] == 1:
          best[encode(row, column)] = 0
          dp[encode(row, column)] = 1
          dq.append((1, row, column))
          
      while len(dq) > 0:
        d, x, y = dq.popleft()
        for xdir, ydir in self.directions:
          nx, ny = x + xdir, y + ydir
          if inside(nx, ny) and cur_board.board[nx][ny] in [0, 1]:
            nd = d + int(cur_board.board[nx][ny] == 0)
            if best[encode(nx, ny)] > nd:
              best[encode(nx, ny)] = nd
              dp[encode(nx, ny)] = 1
              dq.append((nd, nx, ny)) if d != nd else dq.appendleft((nd, nx, ny))
            elif best[encode(nx, ny)] == nd:
              dp[encode(nx, ny)] += dp[encode(x, y)]
      return [best, dp]

    def bfs_multisource_player2(cur_board: HexBoard, row: int):
      best = [self.INF for _ in range(N)]
      dp = [0 for _ in range(N)]
      dq = deque()
      for column in range(cur_board.size):
        if cur_board.board[row][column] == 0:
          best[encode(row, column)] = 0
          dp[encode(row, column)] = 1
          dq.append((1, row, column))
        elif cur_board.board[row][column] == 2:
          best[encode(row, column)] = 1
          dp[encode(row, column)] = 1
          dq.append((1, row, column))          
      while len(dq) > 0:
        d, x, y = dq.popleft()
        for xdir, ydir in self.directions:
          nx, ny = x + xdir, y + ydir
          if inside(nx, ny) and cur_board.board[nx][ny] in [0, 2]:
            nd = d + int(cur_board.board[nx][ny] == 0)
            if best[encode(nx, ny)] > nd:
              best[encode(nx, ny)] = nd
              dp[encode(nx, ny)] = 1
              dq.append((nd, nx, ny)) if d != nd else dq.appendleft((nd, nx, ny))
            elif best[encode(nx, ny)] == nd:
              dp[encode(nx, ny)] += dp[encode(x, y)]
      return [best, dp]
    
    def winner(cur_board: HexBoard, cur_player: int):
      if cur_player == 1:
        best = bfs_multisource_player1(cur_board, 0)
        for i in range(cur_board.size):
          e = encode(i, cur_board.size - 1)
          if best[0][e] == 0:
            return True
      else:
        best = bfs_multisource_player2(cur_board, 0)
        for i in range(cur_board.size):
          e = encode(cur_board.size - 1, i)
          if best[0][e] == 0:
            return True
      return False
    
    # retorna un valor determinado por la ventaja que tiene el jugador 1 sobre el jugador 2
    def heuristic_value(cur_board: HexBoard):
      if winner(cur_board, 1):
        return 100000
    
      if winner(cur_board, 2):
        return 0

      best1 = [bfs_multisource_player1(cur_board, 0), bfs_multisource_player1(cur_board, cur_board.size - 1)]
      best2 = [bfs_multisource_player2(cur_board, 0), bfs_multisource_player2(cur_board, cur_board.size - 1)]

      min_path1, num_path1 = self.INF, 0
      min_path2, num_path2 = self.INF, 0
      for x in range(cur_board.size):
        for y in range(cur_board.size):
          if min_path1 > best1[0][0][encode(x, y)] + best1[1][0][encode(x, y)]:
            min_path1 = best1[0][0][encode(x, y)] + best1[1][0][encode(x, y)]
            num_path1 = best1[0][1][encode(x, y)] * best1[1][1][encode(x, y)]
          elif min_path1 == best1[0][0][encode(x, y)] + best1[1][0][encode(x, y)]:
            num_path1 += best1[0][1][encode(x, y)] * best1[1][1][encode(x, y)]

          if min_path2 > best2[0][0][encode(x, y)] + best2[1][0][encode(x, y)]:
            min_path2 = best2[0][0][encode(x, y)] + best2[1][0][encode(x, y)]
            num_path2 = best2[0][1][encode(x, y)] * best2[1][1][encode(x, y)]
          elif min_path2 == best2[0][0][encode(x, y)] + best2[1][0][encode(x, y)]:
            num_path2 += best2[0][1][encode(x, y)] * best2[1][1][encode(x, y)]

      return 1000 * ((min_path2 + 1) / (min_path1 + 1)) + (num_path1 + 1) / (num_path2 + 1) * 18
    
    def alphaBeta(cur_board: HexBoard, alpha: int, beta: int, cur_player: int, depth: int):
      if time.time() - start_time > time_limit:
        return heuristic_value(cur_board)

      if depth == 0 or winner(cur_board, cur_player) or winner(cur_board, 3 - cur_player):
        return heuristic_value(cur_board)
      
      if cur_player == 1: # max
        opt, cnt = -100000, 0
        movesX = [i for i in range(cur_board.size)]
        for x in movesX:
          movesY = []

          for y in range(cur_board.size):
            if cur_board.board[x][y] != 0:
              continue
            movesY.append(y)

          random.shuffle(movesY)

          for y in movesY:
            if cur_board.board[x][y] != 0:
              continue
            cnt += 1
            cur_board.board[x][y] = cur_player
            go = alphaBeta(cur_board, alpha, beta, 3 - cur_player, depth - 1)
            opt, alpha = max(opt, go), max(alpha, go)
            cur_board.board[x][y] = 0
          if alpha >= beta: break
        return opt
      else: # min
        opt, cnt = 100000, 0
        movesX = [i for i in range(cur_board.size)]
        random.shuffle(movesX)
        for x in movesX:
          movesY = []

          for y in range(cur_board.size):
            if cur_board.board[x][y] != 0:
              continue
            movesY.append(y)

          random.shuffle(movesY)

          for y in movesY:
            cnt += 1
            cur_board.board[x][y] = cur_player
            go = alphaBeta(cur_board, alpha, beta, 3 - cur_player, depth - 1)
            opt, beta = min(opt, go), min(beta, go)
            cur_board.board[x][y] = 0
          if alpha >= beta: break
        return opt

    def optimal_move():
      cur_board = board.clone() 
      best, res, sp = -self.INF, self.INF, self.INF
      moves = []
      for x in range(cur_board.size):
        for y in range(cur_board.size):
          if cur_board.board[x][y] != 0: continue 
          moves.append((x, y))

      random.shuffle(moves)

      for x, y in moves:
        cur_board.board[x][y] = self.player_id
        goab = alphaBeta(cur_board, -self.INF, self.INF, 3 - self.player_id, 2)

        if self.player_id == 2:
          goab = 1000000 - goab

        cur_sp = self.INF; opp_sp = self.INF
        if self.player_id == 1:
          dis = bfs_multisource_player1(cur_board, 0)
          for i in range(cur_board.size):
            e = encode(i, cur_board.size - 1)
            cur_sp = min(cur_sp, dis[0][e])

          dis2 = bfs_multisource_player2(cur_board, 0)
          for i in range(cur_board.size):
            e = encode(cur_board.size - 1, i)
            opp_sp = min(opp_sp, dis2[0][e])
        else:
          dis = bfs_multisource_player2(cur_board, 0)
          for i in range(cur_board.size):
            e = encode(cur_board.size - 1, i)
            cur_sp = min(cur_sp, dis[0][e])
        
          dis1 = bfs_multisource_player1(cur_board, 0)
          for i in range(cur_board.size):
            e = encode(i, cur_board.size - 1)
            opp_sp = min(opp_sp, dis1[0][e])
          
        # print(goab + (N - cur_sp) * 7, cur_sp, x, y)
        if best < goab + (N - cur_sp) * 7 + opp_sp * 5:
          best, res, sp = goab + (N - cur_sp) * 7 + opp_sp * 5, (x, y), cur_sp
        elif best == goab + (N - cur_sp) * 7 + opp_sp * 5:
          if cur_sp > sp:
            sp = cur_sp
            res = (x, y)
        cur_board.board[x][y] = 0
        
      return res

    res = optimal_move()
    # print(time.time() - start_time)
    return res 