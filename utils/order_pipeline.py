# def place_all_orders_in_pipeline(engine, orders, user, current_ts):
#     for order in orders:
#         if order["order_execute_ts"] == current_ts:
#             if order["type"] == "open":
#                 print(f"Placing open order {order['order_id']} for user {user.user_id}")
#                 try:
#                     engine.place_order(user.user_id, order["order_object"], current_ts)
#                 except ValueError as e:
#                     print(f"Error placing order {order['order_id']}: {e}")

#             elif order["type"] == "close":
#                 print(
#                     f"Placing close order {order['order_id']} for user {user.user_id}"
#                 )
#                 try:
#                     engine.close_order(
#                         user.user_id,
#                         order["account_mode"],
#                         order["order_id"],
#                         current_ts,
#                     )
#                 except ValueError as e:
#                     print(f"Error closing order {order.order_id}: {e}")

#             elif order["type"] == "close_all":
#                 print(
#                     f"Placing close all orders for user {user.user_id} in {order['account_mode']} mode"
#                 )
#                 try:
#                     engine.close_all_orders(
#                         user.user_id, order["account_mode"], current_ts
#                     )
#                 except ValueError as e:
#                     print(f"Error closing all orders: {e}")


def place_all_orders_in_pipeline(engine, orders, current_ts):
    for order in orders:
        if order["order_execute_ts"] != current_ts:
            continue
        user = order["user"]

        try:
            if order["type"] == "open":
                print(
                    f"[{current_ts}] OPEN → {order['asset']} | Order ID: {order['order_id']} | User ID: {user.user_id} | Account Mode: {order['account_mode']} | Qty: {order['order_object'].qty}"
                )
                engine.place_order(user.user_id, order["order_object"], current_ts)

            elif order["type"] == "close":
                print(
                    f"[{current_ts}] CLOSE → {order['asset']} | Order ID: {order['order_id']} | User ID: {user.user_id} | Account Mode: {order['account_mode']} | Qty: {order['order_object'].qty}"
                )
                engine.close_order(
                    user.user_id, order["account_mode"], order["order_id"], current_ts
                )

            elif order["type"] == "close_all":
                print(
                    f"[{current_ts}] CLOSE ALL | User ID: {user.user_id} | Account Mode: {order['account_mode']}"
                )
                engine.close_all_orders(user.user_id, order["account_mode"], current_ts)

        except ValueError as e:
            print(f"[{current_ts}] ERROR: {e}")
