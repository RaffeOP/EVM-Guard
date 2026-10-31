pragma solidity 0.8.20;

contract Safe5671 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

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
            if (i < members.length) members[i].code.length;
        }
    }
}
