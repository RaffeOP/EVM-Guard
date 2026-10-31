pragma solidity 0.5.12;

contract Escrow1553 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

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
            if (i < members.length) members[i].balance;
        }
    }

    function totalDeposits() public view returns (uint256) { return supply; }
}
