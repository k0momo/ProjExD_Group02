import os
import time 
import pygame as pg
import sys
import math
from typing import Callable, List

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird(pg.sprite.Sprite):
    """
    こうかとんの実装に関するクラス
    """

    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy:tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Enemy(pg.sprite.Sprite):
    """
    敵に関するクラス
    """
    def __init__(self):
        pass

    def update(self):
        pass


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0 = 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam:
    """
    弾幕に関するクラス
    """
    def __init__(self, bird:Bird, num:int):
        self.bird = bird
        self.num = num

    def gen_beams(self):
        """
        それぞれのビームの角度を計算しタプルで返す
        """
        beams = []
        for angle in range(-50, +51, int(100/(self.num-1))):
            beam = Beam(self.bird, angle)
            beams.append(beam)
        return beams


class Score:
    """
    スコアの計算に関するクラス
    """
    def __init__(self):
        """
        撃ち落とした敵などの数を計算し表示するクラス
        """
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen:pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
        
class Weapon:
    """1種類の武器情報を保持するクラス"""
    
    def __init__(
        self,
        name:str,
        cooldown:float,
        fire_func: Callable[[Bird], List[pg.sprite.Sprite]],
    ) -> None:
        self.name = name 
        self.cooldown = cooldown
        self._fire_func = fire_func
        self._last_fire_time = 0.0
        
    def _ready(self) -> bool:
        """クールダウン経過判定"""
        return time.time() - self._last_fire_time >= self.cooldown 
    
    def fire(self, bird: Bird) -> List[pg.sprite.Sprite]:
        """武器を発射し、生成された弾Spriteを返す"""
        if not self._ready():
            return[]
        self._last_fire_time = time.time()
        return self._fire_func(bird)
    
class WeaponSystem:
    """複数武器を切替・発射するマネージャー。"""
    
    def __init__(self, player: Bird) -> None:
        self._player = player
        self._weapons: list[Weapon] = []
        self._idx = 0  # 現在の武器のインデックス
        
    def add(self, weapon: Weapon) -> None:
        self._weapons.append(weapon)
        
    def next(self) -> None:
        """次の武器に切り替える"""
        if self._weapons:
            self._idx = (self._idx + 1) % len(self._weapons)
            
    @property
    def current(self) -> Weapon:
        return self._weapons[self._idx]
    
    def fire(self) -> List[pg.sprite.Sprite]:
        return self.current.fire(self._player)


def main():
    pg.init()
    pg.display.set_caption("生きろこうかとん！")
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    
    score  = Score()
    beams = pg.sprite.Group()
    bird = Bird(3, (900, 400))

    # 武器システム設定
    weapon_system = WeaponSystem(bird)
    weapon_system.add(Weapon("Beam", 0.15, lambda b: [Beam(b)]))
    weapon_system.add(Weapon("Spread", 0.8, lambda b: NeoBeam(b, 9).gen_beams()))

    clock = pg.time.Clock()
    tmr = 0

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_TAB: # TABキーで武器を切り替え
                    weapon_system.next()
                elif event.key == pg.K_SPACE: # スペースキーで武器を発射
                    beams.add(weapon_system.fire())
                    
        screen.blit(bg_img, [0, 0])
        bird.update(key_lst, screen)
        score.update(screen)
        beams.update()
        beams.draw(screen)
        
        # 現在武器名を表示
        font = pg.font.Font(None, 36)
        hud = font.render(f"Weapon: {weapon_system.current.name}", True, (255, 255, 255))
        screen.blit(hud, (10, 10))
        
        pg.display.update()
        
        if tmr % 31 == 0:
            score.value += 0
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()