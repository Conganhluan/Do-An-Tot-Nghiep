class Helper:

    @staticmethod
    def build_graph(node_num: int, neighbor_num: int) -> dict[int: list]:
    
        # Please enhance the code to ensure there is no pair of nodes having more than or equal to 'limitation' same neighbors
        # limitation = neighbor_num//2

        if node_num % 2 and neighbor_num % 2:
            raise Exception(f"There is no graph available for {node_num} nodes and each node having {neighbor_num} neighbors!")

        neighbor_list : dict[int: list] = {}
        for i in range(node_num):
            neighbor_list[i] = []

        current_check_node = 0
        current_fill_node = 0
        done_check = 0

        # Not enough nodes having enough neighbors
        while done_check < node_num:

            # If current node is full of neighbors already then pass
            if len(neighbor_list[current_fill_node]) == neighbor_num:
                current_fill_node = (current_fill_node + 1) % node_num
                done_check += 1
                continue

            # Check continous nodes to pair new neighbors for current node
            current_check_node = current_fill_node
            while len(neighbor_list[current_fill_node]) != neighbor_num:
                
                # Check the next node
                current_check_node = (current_check_node + 1) % node_num

                # If check node = current node then pass
                if current_check_node == current_fill_node:
                    continue

                # If checked node is full of neighbors already then pass
                elif len(neighbor_list[current_check_node]) == neighbor_num:
                    continue

                neighbor_list[current_fill_node].append(current_check_node)
                neighbor_list[current_check_node].append(current_fill_node)

            current_fill_node = (current_check_node + 1) % node_num
            done_check = 1

        return neighbor_list