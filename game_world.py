# 게임 월드: 레이어별 오브젝트 목록과 충돌 쌍. 수업 LEC15 game_world 에 충돌 처리를 더했다.
world = [[], [], []]  # 0: 바닥과 장애물, 1: 캐릭터와 총알, 2: UI
collision_pairs = {}  # 그룹 이름 -> [a 목록, b 목록]


def add_object(o, depth=1):
    world[depth].append(o)


def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
            remove_collision_object(o)
            return


def update():
    for layer in world:
        for o in layer[:]:
            o.update()


def render():
    for layer in world:
        for o in layer[:]:
            o.draw()


def clear():
    for layer in world:
        layer.clear()
    collision_pairs.clear()


def objects():
    for layer in world:
        yield from layer


def add_collision_pair(group, a, b):
    if group not in collision_pairs:
        collision_pairs[group] = [[], []]
    if a:
        collision_pairs[group][0].append(a)
    if b:
        collision_pairs[group][1].append(b)


def remove_collision_object(o):
    for pairs in collision_pairs.values():
        if o in pairs[0]:
            pairs[0].remove(o)
        if o in pairs[1]:
            pairs[1].remove(o)


def collide(a, b):
    la, ba, ra, ta = a.get_bb()
    lb, bb, rb, tb = b.get_bb()
    return not (la > rb or ra < lb or ta < bb or ba > tb)


def handle_collisions():
    for group, (alist, blist) in collision_pairs.items():
        for a in alist[:]:
            for b in blist[:]:
                # 앞선 충돌 처리에서 빠진 오브젝트(주운 총알 등)는 건너뛴다
                if a not in alist or b not in blist:
                    continue
                if collide(a, b):
                    a.handle_collision(group, b)
                    b.handle_collision(group, a)
