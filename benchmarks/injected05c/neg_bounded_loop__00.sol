pragma solidity 0.5.12;

contract Treasury3605 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 16) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 16; i++) {
            if (i < members.length) members[i].balance;
        }
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
