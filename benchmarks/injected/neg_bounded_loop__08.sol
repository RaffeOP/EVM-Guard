pragma solidity 0.8.20;

contract Wallet9823 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 32) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 32; i++) {
            if (i < members.length) members[i].code.length;
        }
    }
}
